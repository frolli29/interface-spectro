"""Classe Application qui contient des attributs communs à toutes les fenêtres PyQt"""

from configparser import ConfigParser
import os
from pathlib import Path
from PyQt5 import QtWidgets
from datetime import datetime

from subsystems.Instrument import Instrument
from lib.oceandirect.OceanDirectAPI import OceanDirectError
from windows.main_window import MainWindow
from graphic.windows.main_win import Ui_MainWindow

path = Path(__file__)
ROOT_DIR = path.parent.absolute()

def require_spectro_open(func):
    def wrapper(self, *args, **kwargs):
        if self.instrument.state=='open':
            return func(self, *args, **kwargs)
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
        self.get_saving_param_from_file()    #parameters for saving : from file to attribute
        self.win.display_saving_param(self.saving_param)    #display attributes

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
        self.win.intensity_box.stateChanged.connect(self.refresh_saving_param)
        self.win.absorbance_box.stateChanged.connect(self.refresh_saving_param)
        self.win.transmittance_box.stateChanged.connect(self.refresh_saving_param)
        self.win.N_spectra.valueChanged.connect(self.refresh_saving_param)
        self.win.T_sec.valueChanged.connect(self.refresh_saving_param)
        self.win.browse.clicked.connect(self.browse_folder)

        self.win.window_close.connect(self.update_saving_param_in_file)
        #connexions saving param
        #self.win.start_multiple_meas.clicked.connect()
        #self.win.single_meas.clicked.connect()
        """
        self.spectro_settings.clicked.connect(self.OnClick_spectro_settings)
        self.save_button.clicked.connect(self.app.createDirectMeasureFile)  #deux façons de sauver les données"""
        

    def get_saving_param_from_file(self):
        """Gets parameters from settings.ini to attributes of Application"""
        parser = ConfigParser() #getting data from Parser
        parser.read(self.settings)
        #Config for data savings
        self.folder=parser.get('saving', 'folder')       
        self.int_box=tobool(parser.get('saving', 'intensity'))
        self.abs_box=tobool(parser.get('saving', 'absorbance'))    
        self.trans_box=tobool(parser.get('saving', 'transmittance'))
        #Configs for continuous measures
        self.N_spectra=int(parser.get('saving', 'N_spectra'))
        self.time_step_ms=int(1000*float(parser.get('saving', 'time_step_sec')))
        self.saving_param=[self.folder,self.int_box,self.abs_box,self.trans_box,self.N_spectra,self.time_step_ms]

    def refresh_saving_param(self):
        #Config for data savings
        self.folder=self.win.saving_folder.text()
        self.int_box=self.win.intensity_box.isChecked()
        #print(self.int_box)
        self.abs_box=self.win.absorbance_box.isChecked()
        self.trans_box=self.win.transmittance_box.isChecked()
        #Configs for continuous measures
        self.N_spectra=self.win.N_spectra.value()
        self.time_step_ms=self.win.T_sec.value()
        self.saving_param=[self.folder,self.int_box,self.abs_box,self.trans_box,self.N_spectra,self.time_step_ms]
        #self.win.display_saving_param(self.saving_param)

    def update_saving_param_in_file(self):
        """Updates saving parameters in settings.ini file"""
        parser = ConfigParser() #getting data from Parser
        parser.read(self.settings)
        #Config for data savings
        parser.set('saving', 'folder', str(self.folder))       
        parser.set('saving', 'intensity', str(self.int_box)) 
        parser.set('saving', 'absorbance', str(self.abs_box))    
        parser.set('saving', 'transmittance', str(self.trans_box))  
        #Configs for continuous measures
        parser.set('saving', 'N_spectra', str(self.N_spectra))
        parser.set('saving', 'time_step_sec', str(round(self.time_step_ms/1000,3)))
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
        
"""class Data():
    def __init__(self,app):
        #Data object can be 'single' or 'multiple'
        self.app=app
    
    def measure(self):
        if self.app

class SingleMeasure(Data):
    def __init__(self, app):
        super().__init__(app)
    
    def take_measure(self):
        self.app.refresh_saving_param()

        if self.app.
        self.

    def create_single_file(self):
        dt = datetime.now()
        date_text=dt.strftime("%m/%d/%Y %H:%M:%S")
        date_time=dt.strftime("%m-%d-%Y_%Hh%Mmin%Ss")
        name = "meas_"
        header = "Instant measure on Dommino titrator\n"+"date and time : "+str(date_text)+"\n"+"Device : "+self.instrument_id+"\n\n"
        data = ""
        print("saving instant measure - ")

        if self.instrument.state=='open':
            name+="Abs_"
            self.app.instrument.update_infos()
            header+=self.app.instrument.infos

            background = self.instrument.active_background_spectrum
            ref = self.instrument.active_ref_spectrum
            sample = self.instrument.current_intensity_spectrum
            absorbance = self.instrument.current_absorbance_spectrum
            wl = self.instrument.wavelengths
            spectra=[wl,background,ref,sample,absorbance]
            Nc=len(spectra)-1
            if background==None or ref==None: #pas de calcul d'absorbance possible
                data+="lambda(nm)\tsample (unit count)\n"
                for l in range(self.instrument.N_lambda):
                    data+=str(spectra[0][l])+'\t'
                    data+=str(spectra[3][l])+'\n'
            else:
                data+="lambda(nm)\tbackground (unit count)\treference ('')\tsample ('')\tabsorbance (abs unit)\n"
                for l in range(self.instrument.N_lambda):
                    for c in range(Nc):
                        data+=str(spectra[c][l])+'\t'
                    data+=str(spectra[Nc][l])+'\n'
        else:
            header+="Spectrometer closed\n"

        name+=str(date_time)
        output=header+"\n\n"+data
        f_out = open(self.saving_folder+'/'+name+'.txt','w') #création d'un fichier dans le répertoire
        f_out.write(output)
        f_out.close()    

class MultipleMeasure(Data):
    def __init__(self, app):
        super().__init__(app)"""