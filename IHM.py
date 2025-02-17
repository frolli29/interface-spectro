"""Classe IHM qui contient des attributs communs à toutes les fenêtres PyQt"""

from PyQt5 import QtCore

from configparser import ConfigParser
import os
from pathlib import Path
from datetime import datetime

#Instruments
from subsystems.system import System
from subsystems.Instrument import Instrument

#Windows
from windows.main_window import MainWindow
from windows.measure_cfg_window import MeasureConfigWindow
from windows.spectra_window import SpectraWindow
from windows.settings_window import SettingsWindow

path = Path(__file__)
ROOT_DIR = path.parent.absolute()

class IHM:

    app_default_settings = os.path.join(ROOT_DIR, "config/app_default_settings.ini")
    device_ids = os.path.join(ROOT_DIR, "config/device_id.ini")
    
    #Sous sytèmes 
    #On créée les instances de chaque sous système ici. L'état est 'closed' par défaut
    system=System()
    spectro_unit=Instrument()

    instrument_id=''    #SN unknown at opening

    def __init__(self):
        
        parser = ConfigParser()
        parser.read(self.app_default_settings)
        #Config for savings
        self.saving_folder=parser.get('saving parameters', 'folder')       
        #Configs for continuous measures
        self.experience_name=None
        self.description=None
        self.dispense_mode=parser.get('sequence', 'dispense_mode')
        #settings
        self.fibers=parser.get('setup', 'fibers')
        self.measure_cell=parser.get('setup', 'measure cell')
        #measure config
        self.time_step_ms=int(1000*float(parser.get('measure config', 'time_step_sec')))
        self.total_time_sec=int(parser.get('measure config', 'total_time_sec'))
        self.N_spectra=int(parser.get('measure config', 'N_spectra'))
        
        #display timer
        self.timer_display = QtCore.QTimer()
        self.timer_display.setInterval(1000)    #timeout every 1s
        self.timer_display.start()
              
    def updateDefaultParam(self):
        #Updates current parameters as default in file
        parser = ConfigParser()
        parser.read(self.app_default_settings)
        file = open(self.app_default_settings,'r+')
        parser.set('saving parameters','folder',str(self.saving_folder))
        parser.set('custom sequence', 'sequence_file', self.sequence_config_file)
        parser.write(file) 
        file.close()
        print("updates current parameters in default file")

    def createDirectMeasureFile(self):
        dt = datetime.now()
        date_text=dt.strftime("%m/%d/%Y %H:%M:%S")
        date_time=dt.strftime("%m-%d-%Y_%Hh%Mmin%Ss")
        name = "mes_"
        header = "Instant measure on Dommino titrator\n"+"date and time : "+str(date_text)+"\n"+"Device : "+self.instrument_id+"\n\n"
        data = ""
        print("saving instant measure - ")
        #saving pH measure

        if self.spectro_unit.state=='open':
            name+="Abs_"
            header+=("\nSpectrometer : "+str(self.spectro_unit.model)+"\n"
            +"Serial number : "+str(self.spectro_unit.serial_number)+"\n"
            +"Integration time (ms) : "+str(self.spectro_unit.t_int/1000)+"\n"
            +"Averaging : "+str(self.spectro_unit.averaging)+"\n"
            +"Boxcar : "+str(self.spectro_unit.boxcar)+"\n"
            +"Nonlinearity correction usage : "+str(self.spectro_unit.device.get_nonlinearity_correction_usage())+"\n")
            if self.spectro_unit.model!='OceanST':
                header+=("Electric dark correction usage : "+str(self.spectro_unit.device.get_electric_dark_correction_usage())+"\n")
            else:
                header+=("Electric dark correction usage : not supported by device\n")
            header+="Absorbance formula : A = log10[(reference-background)/(sample-background)]\n"    

            background = self.spectro_unit.active_background_spectrum
            ref = self.spectro_unit.active_ref_spectrum
            sample = self.spectro_unit.current_intensity_spectrum
            absorbance = self.spectro_unit.current_absorbance_spectrum
            wl = self.spectro_unit.wavelengths
            spectra=[wl,background,ref,sample,absorbance]
            Nc=len(spectra)-1
            if background==None or ref==None: #pas de calcul d'absorbance possible
                data+="lambda(nm)\tsample (unit count)\n"
                for l in range(self.spectro_unit.N_lambda):
                    data+=str(spectra[0][l])+'\t'
                    data+=str(spectra[3][l])+'\n'
            else:
                data+="lambda(nm)\tbackground (unit count)\treference ('')\tsample ('')\tabsorbance (abs unit)\n"
                for l in range(self.spectro_unit.N_lambda):
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


    ### Gestionnaire des fenêtres ###

    def openMainWindow(self):
        self.mainWindow=MainWindow(self)
        self.mainWindow.show()

    def openConfigWindow(self):
        self.measConfig = MeasureConfigWindow(self)
        self.measConfig.show()

    def openSpectroWindow(self):
        self.spectroWindow = SpectraWindow(self)
        self.spectroWindow.show()

    def openSettingsWindow(self):
        self.settings_win = SettingsWindow(self)
        self.settings_win.show()

if __name__=="main":
    interface = IHM()
    print(interface.saving_folder)