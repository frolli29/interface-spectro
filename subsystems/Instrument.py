"classe Instrument permettant de piloter l'ensemble Spectromètre et lampe"

from lib.oceandirect.OceanDirectAPI import OceanDirectError, OceanDirectAPI
from lib.oceandirect.OceanDirectAPI import Spectrometer
from lib.oceandirect.OceanDirectAPI import FeatureID

from lib.oceandirect.od_logger import od_logger
logger = od_logger()

import numpy as np
import time
from configparser import ConfigParser
import os
from pathlib import Path

from PyQt5 import QtCore

import subsystems.processing as sp

path = Path(__file__)
ROOT_DIR = path.parent.parent.absolute() #répertoire
settings = os.path.join(ROOT_DIR, "settings.ini")

def require_open(func):
    def wrapper(self, *args, **kwargs):
        if self.state=='open':
            return func(self, *args, **kwargs)
    return wrapper

class Instrument(Spectrometer):
    
    def __init__(self):
        self.state='closed'
        #Data
        #All spectra are saved with active corrections. It can be nonlinearity and/or electric dark 
        # when activated via methods "set_nonlinearity_correction_usage" and 
        # "set_electric_dark_correction_usage". None of these are corrected from 
        # the background spectrum. 
        self.dark_spectrum=None
        self.active_background_spectrum=None  #Background Spectrum
        self.active_ref_spectrum=None   #Reference
        self.reference_absorbance=None  #courbe d'absorbance juste après la prise de réf
        self.current_intensity_spectrum=None    #Sample or whatever is in the cell
        self.current_absorbance_spectrum=None   #Absorbance
        self.current_transmittance_spectrum=None
        self.absorbance_spectrum1=None
        self.wavelengths=None
        self.model=''
        self.serial_number=''
        self.acquisition_delay=3000
        
        self.refresh_rate=self.acquisition_delay+2000

        #timer pour acquisition des spectres
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.refresh_rate)
        
        self.update_infos()

    def connect(self):
        self.od = OceanDirectAPI() #instance de la classe OceanDirectAPI
        device_count = self.od.find_usb_devices() #ne pas enlever cette ligne pour détecter le spectro
        device_ids = self.od.get_device_ids()
        if device_ids!=[]:
            self.id=device_ids[0]
            try:
                spectro = self.od.open_device(self.id) #crée une instance de la classe Spectrometer
                adv = Spectrometer.Advanced(spectro)
                self.state='open' 
            except:
                self.state='closed'
                print("Can not connect to spectrometer identified : ",self.id)
        else:
            self.state='closed'
            print('No spectrometer detected')
        if self.state=='open':
            self.spectro=spectro    #instanciation de spectro et adv comme attributs de la classe
            self.adv=adv    #instance for advanced features
        
    
    @require_open
    def configure(self):
        self.wavelengths = [ round(l,2) for l in self.spectro.wavelengths ]
        self.N_lambda = len(self.wavelengths)
        self.model=self.spectro.get_model()
        self.serial_number=self.spectro.get_serial_number()
        
        parser = ConfigParser()
        parser.read(settings)
        former_model=parser.get('spectrometer', 'model')
        
        ##Settings specific to models 

        #time attributes in milliseconds. SDK methods outputs are in microseconds (us)
        self.t_int_min_us=self.spectro.get_minimum_integration_time() 
        self.t_int_max_us=self.spectro.get_maximum_integration_time() 
        self.dt_int_us=self.spectro.get_integration_time_increment()    #us
        if self.model==former_model:
            self.t_int_us=int(parser.get('spectrometer', 'tint_us'))  #us
            self.averaging=int(parser.get('spectrometer', 'avg'))
            self.spectro.set_integration_time(self.t_int_us) #input in us
            self.spectro.set_scans_to_average(self.averaging)
        else:
            self.spectro.set_integration_time(self.t_int_min_us) 
            self.spectro.set_scans_to_average(1)
        
        self.t_int_us=self.spectro.get_integration_time()
        self.averaging=self.spectro.get_scans_to_average()
        self.acquisition_delay=self.t_int_us*self.averaging    #us
        self.boxcar=self.spectro.get_boxcar_width()
        
        if self.model=='OceanSR2':  #2k pix pour 700nm
            self.spectro.set_boxcar_width(1) #moyennage sur 3 points (2n+1)    
        elif self.model=='OceanSR6':    #2k pix pour 700nm à vérifier pour le SR6
            self.spectro.set_boxcar_width(1) #moyennage sur 3 points (2n+1)
        elif self.model=='OceanST': #2k pix pour 400nm
            self.spectro.set_boxcar_width(2) #moyennage sur 5 points (2n+1) 
        elif self.model=='HR2000+':
            self.spectro.set_boxcar_width(4) #moyenne sur 9 points (2k pixels sur 200nm soit 10 valeurs /nm)
        else:
            print("No boxcar value selected")
        
        #stores dark in buffer to allow electric dark and nonlinearity correction ? Test
        self.acquire_dark() 
        
        disable_nl_corr=False
        try:    
            self.spectro.set_nonlinearity_correction_usage(True)
            self.nl_corr=True
        except:
            self.nl_corr=False
            disable_nl_corr=True
            print("Nonlinearity correction not supported by device")
        
        disable_ed_corr=False
        try:
            self.spectro.set_electric_dark_correction_usage(True)
            self.ed_corr=True
        except:
            self.ed_corr=False
            disable_ed_corr=True
            print("Electric dark correction not supported by device")
        #GPIO
        self.N_gpio=self.adv.get_gpio_pin_count()
        print('N gpio',self.N_gpio)
        self.gpio_states=[self.adv.gpio_get_value1(k) for k in range(self.N_gpio)]
        print('gpio states = ', self.gpio_states)
        
        self.timer.start()
        self.timer.timeout.connect(self.updateSpectra)
        
        self.update_infos(disp=True)
        
        return disable_nl_corr, disable_ed_corr
    
    def update_infos(self,disp=False):
        if self.state=='open':
            self.infos=("\nSpectrometer : Connected"\
            +"\nModel : "+self.model\
            +"\nSerial number : "+self.serial_number\
            +"\nIntegration time (ms) : "+str(self.t_int_us/1000)\
            +"\nAveraging : "+str(self.averaging)\
            +"\nBoxcar : "+str(self.boxcar)\
            +"\nNonlinearity correction usage : "+str(self.nl_corr)\
            +"\nElectric dark correction usage : "+str(self.ed_corr)\
            +"\nAbsorbance formula : A = log10[(reference-background)/(sample-background)]"\
            +"\nTransmittance formula : T = (sample-background)/(reference-background)")
        else:
            self.infos="\nSpectrometer : Not connected"
        if disp==True:
            print(self.infos)

    def close(self,id): #fermeture de l'objet Instrument
        self.timer.stop()
        self.set_shutter_state(False)
        self.update_default_param()
        print("updating current paramters")
        self.spectro.close_device()
        self.od.close_device(id) #close_device(id)
        print("Spectrometer disconnected\n")
        self.state='closed'
    
    def update_default_param(self):
        parser = ConfigParser()
        parser.read(settings)
        parser.set('spectrometer', 'model', str(self.model))
        parser.set('spectrometer', 'SN', str(self.serial_number))
        parser.set('spectrometer', 'tint_us', str(self.spectro.get_integration_time()))
        parser.set('spectrometer', 'avg', str(self.spectro.get_scans_to_average()))
        parser.set('spectrometer', 'processing_rate_sec', str(self.refresh_rate))
        parser.set('spectrometer', 'boxcar', str(self.boxcar))
        parser.set('spectrometer', 'ed_corr', str(self.ed_corr))
        parser.set('spectrometer', 'nl_corr', str(self.nl_corr))
        file = open(settings,'r+')
        parser.write(file)
        file.close()

    def get_shutter_state(self):
        if self.state=='open':
            self.shutter=self.adv.get_enable_lamp()
        else:
            self.shutter=False
        return self.shutter
    
    @require_open
    def set_shutter_state(self,state):
        self.adv.set_enable_lamp(state)
        if state==True:
            print("shutter open")
        else:
            print("shutter closed\n")
    
    def change_shutter_state(self):
        shutter=self.get_shutter_state()
        self.set_shutter_state(not(shutter))
    
    def update_acquisition_delay(self):
        self.acquisition_delay=self.t_int*self.averaging #ms

    #Récupère autant de spectres que N_avg sur le spectro
    #Fonction vérifiée qui fonctionne. Plus rapide que de faire le moyennage sur le spectro
    def get_N_spectra(self):
        N=self.spectro.get_scans_to_average()
        try:
            self.spectro.set_scans_to_average(1)
            spectra = [0 for k in range(N)]
            for i in range(N):
                spectra[i] = self.spectro.get_formatted_spectrum() #gets the current spectrum
                # with activated corrections (nonlinearity and/or electric dark) and with
                # NO substraction of the background
            for spec in spectra:
                for i in spec:
                    i=round(i,2)
            self.spectro.set_scans_to_average(N)
        except OceanDirectError as e:
            logger.error(e.get_error_details())  
        #☺print("spectra",spectra)
        return spectra
    
    def get_averaged_spectrum(self):
        """Returns a list of float"""
        t0=time.time()
        spectra=self.get_N_spectra()
        t1=time.time()
        avg=sp.average_spectra(spectra)
        t2=time.time()
        self.Irec_time=t1-t0
        self.avg_delay=t2-t1
        self.update_refresh_rate()
        return avg

    @require_open
    def acquire_dark(self):
        self.set_shutter_state(False)
        time.sleep(1)
        self.dark_spectrum=self.get_averaged_spectrum()
        self.spectro.set_stored_dark_spectrum(self.dark_spectrum)

    @require_open
    def acquire_background(self):
        self.set_shutter_state(False)
        time.sleep(1)
        self.active_background_spectrum=self.get_averaged_spectrum()

    @require_open
    def acquire_reference(self):
        self.set_shutter_state(True)
        time.sleep(1)
        ref=self.get_averaged_spectrum()
        ref2=self.get_averaged_spectrum()
        self.active_ref_spectrum=ref
        bgd=self.active_background_spectrum
        if bgd!=None:
            self.reference_absorbance, self.Aproc_delay = sp.intensity2absorbance(ref2,ref,bgd)

    def update_intensity_spectrum(self):    #ontimer
        self.current_intensity_spectrum=self.get_averaged_spectrum()
    
    def update_absorbance_spectrum(self):
        self.current_absorbance_spectrum, self.Aproc_delay = sp.intensity2absorbance(self.current_intensity_spectrum,self.active_ref_spectrum,self.active_background_spectrum)

    def update_current_transmittance_spectrum(self):
        self.current_transmittance_spectrum, self.Tproc_delay = sp.intensity2transmittance(self.current_intensity_spectrum,self.active_ref_spectrum,self.active_background_spectrum)

    def dark_and_ref_stored(self):
        """Returns True if a background and a reference spectrum have been stored, False otherwise"""
        open=(self.state=='open')
        bgd=(self.active_background_spectrum!=None)
        ref=(self.active_ref_spectrum!=None)
        return open*bgd*ref

    def updateSpectra(self):
        self.update_intensity_spectrum()
        if self.dark_and_ref_stored(): #background and ref recorded
            self.update_absorbance_spectrum()
            self.update_current_transmittance_spectrum()

    #@Necessary that background and ref are stored
    def update_refresh_rate(self):   
        self.refresh_rate=int(self.Irec_time*1000)+500   #ms
        self.timer.setInterval(self.refresh_rate)

    ### Fonctions avancées    
    def get_optimal_integration_time(self, spectra):
        int_time_us=self.t_int*1000
        Imax=sp.max_intensity(spectra)
        if self.serial_number=='STUV002':
            optimal_int_time_us = 1000*int(int_time_us*15/Imax) #15000 unit count correspond au ST.
            #Le capteur a une résolution de 14bit = 16300... unit count
            #ça doit être un multiple de 1000 pour être entier en millisecondes.
            return optimal_int_time_us  
        elif self.serial_number=='SR200336':
            optimal_int_time_us = 1000*int(int_time_us*50/Imax) #15000 unit count correspond au ST. 
            return optimal_int_time_us
        else:
            print("numéro du spectro: ",self.serial_number)
        return optimal_int_time_us

