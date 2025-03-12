"""Classe Application qui contient des attributs communs à toutes les fenêtres PyQt"""

from configparser import ConfigParser
import os
from pathlib import Path
from PyQt5 import QtWidgets, QtCore
from datetime import datetime
import time

from subsystems.Instrument import Instrument
from lib.oceandirect.OceanDirectAPI import OceanDirectError
import subsystems.processing as proc
from windows.main_window import MainWindow
from graphic.windows.main_win import Ui_MainWindow

path = Path(__file__)
ROOT_DIR = path.parent.absolute()

def require_spectro_open(func):
    def wrapper(self, *args, **kwargs):
        if self.instrument.state=='open':
            return func(self, *args, **kwargs)
        else:
            print("instrument close")
    return wrapper

def time_us_to_ms(t_us:int,step_us:int):
    """Returns the closest time in milliseconds multiple of increment"""
    t_ms=round((t_us//step_us)*step_us/1000,3)
    #print(t_ms)
    return t_ms

def time_ms_to_us(t_ms:float,step_us:int):
    """Returns the closest time in microsecond multiple of increment"""
    t_us = (int(t_ms*1000)//step_us)*step_us   #is multiple of increment is us
    #print(t_us)
    return t_us

def tobool(str):
    if str=='True' or str=='true':
        b=True
    else:
        b=False
    return b

class Application():

    settings = os.path.join(ROOT_DIR, "settings.ini")

    def __init__(self, instrument:Instrument, win:MainWindow) -> None:
        #Attributes
        self.instrument=instrument
        self.win=win
        self.measure_timer = QtCore.QTimer()

        self.get_saving_param_from_file()    #parameters for saving : from file to attribute
        self.win.display_saving_param(self.saving_param)    #display attributes

        #Measure timer
        self.measure_timer.setInterval(self.time_step_ms)
        self.measure_timer.start()
        
        #affichage
        self.win.display_connexion_state('closed')

        #connexions
        self.win.connect_disconnect_spectro_button.clicked.connect(self.connect_disconnect_spectrometer)
        self.win.shutter.stateChanged.connect(self.change_shutter_state)
        self.win.refresh_background.clicked.connect(lambda:self.instrument.acquire_background())
        self.win.refresh_reference.clicked.connect(lambda:self.instrument.acquire_reference())
        self.win.Tint.valueChanged.connect(lambda: self.change_tint())
        self.win.avg.valueChanged.connect(lambda: self.change_avg())
        self.win.NLcorr_box.stateChanged.connect(lambda: self.change_NL_corr())
        self.win.EDcorr_box.stateChanged.connect(lambda: self.change_ED_corr())
        #saving param
        self.win.saving_folder.textChanged.connect(self.refresh_saving_param)
        self.win.basename.textChanged.connect(self.refresh_saving_param)
        self.win.intensity_box.stateChanged.connect(self.refresh_saving_param)
        self.win.absorbance_box.stateChanged.connect(self.refresh_saving_param)
        self.win.transmittance_box.stateChanged.connect(self.refresh_saving_param)
        self.win.N_spectra.valueChanged.connect(self.refresh_saving_param)
        self.win.T_sec.valueChanged.connect(self.refresh_saving_param)
        self.win.browse.clicked.connect(self.browse_folder)
        self.win.window_close.connect(self.update_saving_param_in_file)
        #measure
        self.win.start_multiple_meas.clicked.connect(self.take_multiple_measure)
        self.win.single_meas.clicked.connect(self.take_single_measure)

    def get_saving_param_from_file(self):
        """Gets parameters from settings.ini to attributes of Application"""
        parser = ConfigParser() #getting data from Parser
        parser.read(self.settings)
        #Config for data savings
        self.folder=parser.get('saving', 'folder')      
        self.basename=parser.get('saving', 'name') 
        self.int_box=tobool(parser.get('saving', 'intensity'))
        self.abs_box=tobool(parser.get('saving', 'absorbance'))    
        self.trans_box=tobool(parser.get('saving', 'transmittance'))
        #Configs for continuous measures
        self.N_meas=int(parser.get('saving', 'n_spectra'))
        self.time_step_ms=int(1000*float(parser.get('saving', 'time_step_sec')))
        self.saving_param=[self.folder,self.basename,self.int_box,self.abs_box,self.trans_box,self.N_meas,self.time_step_ms]

    def refresh_saving_param(self):
        """Stores current parameters of interface as attributes of Class Application"""
        #Config for data savings
        self.folder=self.win.saving_folder.text()
        self.basename=self.win.basename.text()
        self.int_box=self.win.intensity_box.isChecked()
        #print(self.int_box)
        self.abs_box=self.win.absorbance_box.isChecked()
        self.trans_box=self.win.transmittance_box.isChecked()
        #Configs for continuous measures
        self.N_meas=self.win.N_spectra.value()
        self.time_step_ms=self.win.T_sec.value()
        self.saving_param=[self.folder,self.int_box,self.abs_box,self.trans_box,self.N_meas,self.time_step_ms]
        #self.win.display_saving_param(self.saving_param)

    def update_saving_param_in_file(self):
        """Updates saving parameters in settings.ini file"""
        parser = ConfigParser() #getting data from Parser
        parser.read(self.settings)
        #Config for data savings
        parser.set('saving', 'folder', str(self.folder))       
        parser.set('saving', 'name', str(self.basename))       
        parser.set('saving', 'intensity', str(self.int_box)) 
        parser.set('saving', 'absorbance', str(self.abs_box))    
        parser.set('saving', 'transmittance', str(self.trans_box))  
        #Configs for continuous measures
        parser.set('saving', 'n_spectra', str(self.N_meas))
        parser.set('saving', 'time_step_sec', str(round(self.time_step_ms/1000,3)))
        time.sleep(1)
        file = open(self.settings,'w')
        parser.write(file)
        file.close()
        print("updates saving params in file")
    
    def browse_folder(self):
        parser = ConfigParser()
        parser.read(self.settings)
        fld=parser.get('saving', 'folder')  #affichage par défaut
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self.win, 'Select Folder', fld)
        self.win.saving_folder.setText(folderpath) #affichage du chemin de dossier
        self.folder=folderpath
        self.refresh_saving_param()

    ### Methods for Spectrometer
    def connect_disconnect_spectrometer(self):
        state=self.instrument.state
        if state=='closed':
            self.instrument.connect()
            if self.instrument.state=='open':
                self.nl_corr_disabled, self.ed_corr_disabled = self.instrument.configure()
        elif state=='open':
            self.instrument.close(self.instrument.id)
        state=self.instrument.state
        self.win.display_connexion_state(state)
        if state=='open':
            #affichage lors de la connexion
            self.win.label_model.setText("model : "+self.instrument.model)
            self.win.label_spectro_SN.setText("S/N : "+self.instrument.serial_number)
            
            #print(self.instrument.t_int_min_us)
            self.win.Tint.setSingleStep(time_us_to_ms(self.instrument.dt_int_us,self.instrument.dt_int_us))
            self.win.Tint.setMinimum(time_us_to_ms(self.instrument.t_int_min_us,self.instrument.dt_int_us))
            self.win.Tint.setMaximum(time_us_to_ms(self.instrument.t_int_max_us,self.instrument.dt_int_us))
            self.win.Tint.setValue(time_us_to_ms(self.instrument.t_int_us,self.instrument.dt_int_us))
            self.win.avg.setValue(self.instrument.averaging)
            self.win.NLcorr_box.setDisabled(self.nl_corr_disabled)
            self.win.EDcorr_box.setDisabled(self.ed_corr_disabled)
            self.win.NLcorr_box.setChecked(self.instrument.nl_corr)
            self.win.EDcorr_box.setChecked(self.instrument.ed_corr)

            #config de l'affichage du spectre courant
            self.win.lambdas=self.instrument.wavelengths      
            #mise sur timer
            self.instrument.timer.timeout.connect(self.updateSpectrum)            
            #état réel du shutter
            #self.win.shutter.setChecked(not(self.instrument.get_shutter_state()))
            #self.win.shutter.clicked.connect(self.instrument.change_shutter_state)

    def updateSpectrum(self):
        if self.instrument.state == 'open' and self.instrument.current_intensity_spectrum!=None:   #intensité direct
            self.win.intensity_direct_plot=self.win.Spectrum_direct.plot([0],[0],clear = True)
            self.win.intensity_direct_plot.setData(self.win.lambdas,self.instrument.current_intensity_spectrum)
        if self.instrument.active_ref_spectrum!=None:
            self.win.reference_plot=self.win.Spectrum_direct.plot([0],[0],pen='g')
            self.win.reference_plot.setData(self.win.lambdas,self.instrument.active_ref_spectrum)
        if self.instrument.active_background_spectrum!=None:      
            self.win.background_plot=self.win.Spectrum_direct.plot([0],[0],pen='r')
            self.win.background_plot.setData(self.win.lambdas,self.instrument.active_background_spectrum)
        if self.instrument.current_absorbance_spectrum!=None: #abs direct
            self.win.abs_direct_plot=self.win.Abs_direct.plot([0],[0],clear = True)
            self.win.abs_direct_plot.setData(self.win.lambdas,self.instrument.current_absorbance_spectrum)
        if self.instrument.reference_absorbance!=None:    #abs ref
            self.win.reference_abs_plot=self.win.Abs_direct.plot([0],[0],pen='y')
            self.win.reference_abs_plot.setData(self.win.lambdas,self.instrument.reference_absorbance)
        if self.instrument.current_transmittance_spectrum!=None:
            self.win.trans_direct_plot=self.win.Transmittance_direct.plot([0],[0],clear = True)
            self.win.trans_direct_plot.setData(self.win.lambdas,self.instrument.current_transmittance_spectrum)
    
    def change_shutter_state(self):
        #state=self.win.shutter.isChecked
        self.instrument.change_shutter_state()
        #self.win.shutter.setChecked(self.instrument.shutter)

    @require_spectro_open
    def change_tint(self):
        """Sets the spectrometer integration time (us) according to visible value on window"""
        tint_us=time_ms_to_us(self.win.Tint.value(),self.instrument.dt_int_us)
        self.instrument.spectro.set_integration_time(tint_us)
    
    @require_spectro_open
    def change_avg(self):
        """Sets the spectrometer averaging according to visible value on window"""
        avg=self.win.avg.value()
        self.instrument.spectro.set_scans_to_average(avg)
    
    @require_spectro_open
    def change_NL_corr(self):
        """Sets the spectrometer nonlinearity correction usage according to visible value on window"""
        self.instrument.nl_corr=self.win.NLcorr_box.isChecked()
        self.instrument.spectro.set_nonlinearity_correction_usage(self.instrument.nl_corr)
    
    @require_spectro_open
    def change_ED_corr(self):
        """Sets the spectrometer electric dark correction usage according to visible value on window"""
        self.instrument.ed_corr=self.win.EDcorr_box.isChecked()
        try:
            self.instrument.spectro.set_electric_dark_correction_usage(self.instrument.ed_corr)
        except:
            print("Electric dark correction not supported by device")
            self.win.EDcorr_box.setChecked(False)

    def refresh_screen(self,state):
        if state=='open':
            self.refreshShutterState()

    def closeEvent(self, event):
        print("Closing main window")
        self.refresh_saving_param()
        self.update_saving_param_in_file()
    
    def take_single_measure(self):
        if self.instrument.state=='open':
            self.refresh_saving_param()
            self.dt = datetime.now()
            self.intensity_spectrum = self.instrument.get_averaged_spectrum()
            if self.instrument.dark_and_ref_stored():
                self.absorbance_spectrum, t_abs = proc.intensity2absorbance(self.intensity_spectrum,self.instrument.active_ref_spectrum,self.instrument.active_background_spectrum)
                self.transmittance_spectrum, t_trans = proc.intensity2transmittance(self.intensity_spectrum,self.instrument.active_ref_spectrum,self.instrument.active_background_spectrum)
            self.create_single_file()

    def take_multiple_measure(self):
        """Creates a file with all the spectra for each type of spectra"""
        if self.instrument.state=='open':
            self.refresh_saving_param()
            self.intensity_spectra = []
            self.absorbance_spectra = []
            self.transmittance_spectra = []
            self.measure_times=[]
            self.measure_index=0
            self.take_measure_k()

    def wait_for_next_measure(self):
        self.measure_timer.singleShot(self.time_step_ms,self.take_measure_k)
    
    def take_measure_k(self):
        if self.instrument.state=='open':
            self.measure_index+=1
            self.dt = datetime.now()
            self.measure_times.append(self.dt)
            self.intensity_spectrum = self.instrument.get_averaged_spectrum()
            self.intensity_spectra.append(self.intensity_spectrum)
            if self.instrument.dark_and_ref_stored():
                self.absorbance_spectrum, t_abs = proc.intensity2absorbance(self.intensity_spectrum,self.instrument.active_ref_spectrum,self.instrument.active_background_spectrum)
                self.transmittance_spectrum, t_trans = proc.intensity2transmittance(self.intensity_spectrum,self.instrument.active_ref_spectrum,self.instrument.active_background_spectrum)
                self.absorbance_spectra.append(self.absorbance_spectrum)
                self.transmittance_spectra.append(self.transmittance_spectrum)
            if self.measure_index<self.N_meas:
                self.wait_for_next_measure()
            else:   #last measure
                self.create_multiple_measure_files()
                
    def create_single_file(self):

        date_text=self.dt.strftime("%m/%d/%Y %H:%M:%S")
        date_time=self.dt.strftime("%m-%d-%Y_%Hh%Mmin%Ss")
        name = self.basename+"_meas_"

        print("saving instant measure - ",date_text)

        if self.instrument.state=='open':
            header = "Single measure\n"+"date and time : "+str(date_text)+"\n"
            self.instrument.update_infos()
            header+=self.instrument.infos
            data="lambda(nm)\t"
            spectra=[self.instrument.wavelengths]
            if self.instrument.dark_and_ref_stored():
                data+="\tbackground (unit count)\treference ('')"
                spectra.append(self.instrument.active_background_spectrum)
                spectra.append(self.instrument.active_ref_spectrum)
            if self.int_box:
                name+="Intens_"
                data+="\tintensity ('')"
                spectra.append(self.intensity_spectrum)    
            if self.instrument.dark_and_ref_stored():   
                if self.abs_box:
                    name+="Absorb_"
                    data+="\tabsorbance (OD)"
                    spectra.append(self.absorbance_spectrum)
                if self.trans_box:
                    name+="Transmit_"
                    data+="\ttransmittance (%)"
                    spectra.append(self.transmittance_spectrum)
            data+="\n"
            N_spec=len(spectra)-1
            print(N_spec)
            for l in range(self.instrument.N_lambda):
                for c in range(N_spec):
                    #print(l,c)
                    data+=str(spectra[c][l])+'\t'
                data+=str(spectra[N_spec][l])+'\n'
        else:
            header+="Spectrometer closed\n"

        name+=str(date_time)
        output=header+"\n\n"+data
        f_out = open(self.folder+'/'+name+'.txt','w') #création d'un fichier dans le répertoire
        f_out.write(output)
        f_out.close()    

    def create_multiple_measure_files(self):
        """For each spectrum type (intensity, absorbance and transmittance) one file is created
        Each file contains informations on system's current state
        File intensity contains background and reference spectra"""
        
        self.refresh_saving_param()

        dt = datetime.now()
        date_text=dt.strftime("%m/%d/%Y %H:%M:%S")
        date_time=dt.strftime("%m-%d-%Y_%Hh%Mmin%Ss")
        name = self.basename+"_multiple_measure_"
        print("saving instant measure - ",date_text)

        if self.instrument.state=='open':

            self.instrument.update_infos()
            header = ("Multiple measure\n"+"Start time : "+str(date_text)
            +"\nNumber of measures :"+str(self.N_meas)+"\nTime interval (ms) : "
            +str(self.time_step_ms)+"\n\n"+self.instrument.infos)
                                
                                ### Intensity spectra
            if self.int_box:
                header_intensity="Intensity spectra (unit counts)\n"+header
                spectra_intensity=[self.instrument.wavelengths]
                data_intensity="lambda(nm)\t"
                if self.instrument.dark_and_ref_stored():
                    data_intensity+="background (unit count)\treference ('')"
                    spectra_intensity.append(self.instrument.active_background_spectrum)
                    spectra_intensity.append(self.instrument.active_ref_spectrum)
                for n in range(len(self.intensity_spectra)):
                    data_intensity+="\t"+str(n+1)
                data_intensity+='\n'
                spectra_intensity+=self.intensity_spectra   #all spectra
                #print("len spectra",len(spectra_intensity))
                #print("Nmeas",self.N_meas)
                #add text
                n_col=1+2*self.instrument.dark_and_ref_stored()+self.N_meas #number of columns
                #print("ncol",n_col)
                for l in range(self.instrument.N_lambda):
                    for c in range(n_col):
                        #print(l,c)
                        data_intensity+=str(spectra_intensity[c][l])+'\t'
                    data_intensity+='\n'
                name_intensity = name+"intensity_"+str(date_time)
                self.write_file(name_intensity,header_intensity,data_intensity)
            
            if self.instrument.dark_and_ref_stored():   
                                ### Absorbance spectra
                if self.abs_box:
                    header_absorbance="Absorbance spectra (OD)\n"+header
                    spectra_absorbance=[self.instrument.wavelengths]
                    spectra_absorbance+=self.absorbance_spectra
                    data_absorbance="lambda(nm)"
                    for n in range(len(self.absorbance_spectra)):
                        data_absorbance+="\t"+str(n+1)
                    data_absorbance+="\n"
                    #add text
                    n_col=1+self.N_meas #number of columns
                    for l in range(self.instrument.N_lambda):
                        for c in range(n_col):
                            #print(l,c)
                            data_absorbance+=str(spectra_absorbance[c][l])+'\t'
                        data_absorbance+='\n'
                    name_absorbance = name+"absorbance_"+str(date_time)
                    self.write_file(name_absorbance,header_absorbance,data_absorbance)

                if self.trans_box:
                    header_transmittance="Transmittance spectra (%)\n"+header
                    spectra_transmittance=[self.instrument.wavelengths]+self.transmittance_spectra
                    data_transmittance="lambda(nm)"
                    for n in range(len(self.transmittance_spectra)):
                        data_transmittance+="\t"+str(n+1)
                    data_transmittance+="\n"
                    #add text
                    n_col=1+self.N_meas #number of columns
                    for l in range(self.instrument.N_lambda):
                        for c in range(n_col):
                            #print(l,c)
                            data_transmittance+=str(spectra_transmittance[c][l])+'\t'
                        data_transmittance+='\n'
                    name_transmittance = name+"transmittance_"+str(date_time)
                    self.write_file(name_transmittance,header_transmittance,data_transmittance)
        else:
            header+="Spectrometer closed\n"


    def write_file(self,name,header,data):
        output=header+"\n\n"+data
        f_out = open(self.folder+'/'+name+'.txt','w') #création d'un fichier dans le répertoire
        f_out.write(output)
        f_out.close()