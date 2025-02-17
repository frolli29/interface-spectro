"Classe de la fenêtre pour gestion spectromètre et lampe"

from lib.oceandirect.OceanDirectAPI import OceanDirectError, OceanDirectAPI, Spectrometer as Sp
from lib.oceandirect.od_logger import od_logger
from subsystems.Instrument import Instrument
import subsystems.processing as proc

from PyQt5 import QtCore, QtGui, QtWidgets
from graphic.windows.spectra_win import Ui_spectra
from PyQt5.QtWidgets import QDialog

_translate = QtCore.QCoreApplication.translate

from configparser import ConfigParser
import os
from pathlib import Path

path = Path(__file__)
ROOT_DIR = path.parent.absolute()
app_default_settings = os.path.join(ROOT_DIR, "../config/app_default_settings.ini")

class SpectraWindow(QDialog,Ui_spectra):

    def __init__(self, ihm, parent=None):
        super(SpectraWindow,self).__init__(parent)
        self.setupUi(self)
        self.spectro_unit=ihm.spectro_unit
        self.ihm=ihm
    
        self.refreshing_rate=1000 #ms

        #spectro connecté
        if self.spectro_unit.state=='open':
            self.shutter.setChecked(self.spectro_unit.shutter.getState())  
            self.NLcorr_box.setChecked(self.spectro_unit.device.get_nonlinearity_correction_usage())
            if self.spectro_unit.model=='OceanST' or self.spectro_unit.model=='OceanSR6':
                self.EDcorr_box.setDisabled(True)
            else:
                self.EDcorr_box.setChecked(self.spectro_unit.device.get_electric_dark_correction_usage())
                self.EDcorr_box.clicked.connect(self.change_EDcorr_state)
            
            self.lambdas=self.spectro_unit.wavelengths

            #Affichage des paramètres selon valeurs actuelles du spectro
            device = "device model : "+self.spectro_unit.model
            self.label_model.setText(device)
            if self.spectro_unit.model=='OceanSR6':
                self.Tint.setMinimum(self.spectro_unit.device.get_minimum_integration_time()//1000+1) #milliseconds
                self.Tint.setMaximum(self.spectro_unit.device.get_maximum_integration_time()//1000)
            if self.spectro_unit.model=='OceanST':
                self.Tint.setMinimum(self.spectro_unit.device.get_minimum_integration_time()//1000+1) #milliseconds
                self.Tint.setMaximum(self.spectro_unit.device.get_maximum_integration_time()//1000)
            self.Tint.setProperty("value", self.spectro_unit.t_int)  
            self.avg.setProperty("value", self.spectro_unit.averaging)
            self.acquisition_delay_display.setText(_translate("Dialog", "acquisition delay : %0.2f seconds"% float(self.spectro_unit.acquisition_delay/1000) ))

            #connexions
            self.Tint.valueChanged.connect(self.update_integration_time)
            self.avg.valueChanged.connect(self.update_averaging)
            self.shutter.clicked.connect(self.changeShutterState)
            #enregistrement
            self.refresh_background.clicked.connect(self.spectro_unit.acquire_background_spectrum)
            self.refresh_background.clicked.connect(self.refreshShutterState)
            self.refresh_ref.clicked.connect(self.spectro_unit.acquire_ref_spectrum)
            self.refresh_ref.clicked.connect(self.refreshShutterState)
            
            #actualisation des spectres périodiquement
            self.spectro_unit.timer.timeout.connect(self.refreshScreen)

            #Clic sur OK
            self.buttonBox.accepted.connect(self.updateDefaultParameters)
    
    def refreshScreen(self):  
        bgd=(self.spectro_unit.active_background_spectrum!=None)
        ref=(self.spectro_unit.active_ref_spectrum!=None)
        
        #Actu des graphes
        #Intensity
        self.intensity_plot=self.intensity_widget.plot([0],[0],pen="r",clear = True)
        self.intensity_plot.setData(self.lambdas,self.spectro_unit.current_intensity_spectrum)
        if bgd: #background enregistré
            a=self.background_widget.plot([0],[0],clear = True)
            self.dark_plot=a
            self.dark_plot.clear()
            self.dark_plot.setData(self.lambdas,self.spectro_unit.active_background_spectrum) 
        if ref: #réf enregistrée
            self.ref_plot=self.reference_widget.plot([0],[0],pen="g",clear = True)
            self.ref_plot.setData(self.lambdas,self.spectro_unit.active_ref_spectrum)
        if bgd*ref: #absorbance
            self.abs_plot=self.absorbance_widget.plot([0],[0],pen="y",clear = True)
            self.abs_plot.setData(self.lambdas,self.spectro_unit.current_absorbance_spectrum)
            delay_sec=float(self.spectro_unit.Aproc_delay/1000) 
            self.absorbance_processing_delay_display.setText("Absorbance computation delay : %f seconds" %delay_sec)

        #actu des delays
        self.acquisition_delay_display.setText(_translate("Dialog", "acquisition delay : %0.2f seconds"% float(self.spectro_unit.acquisition_delay/1000) ))
        self.recording_delay_display.setText("processing delay : %f seconds" %self.spectro_unit.Irec_time)
        self.averaging_delay_display.setText("averaging delay : %f seconds" %self.spectro_unit.avg_delay)          
        self.refresh_rate_display.setText(_translate("Dialog", "période de rafraîchissement : %0.2f seconds"% float(self.spectro_unit.refresh_rate/1000) ))   

        #shutter
        self.refreshShutterState()

    def changeShutterState(self):
        self.spectro_unit.changeShutterState()
        self.refreshShutterState()

    def refreshShutterState(self):
        self.shutter.setChecked(not(self.spectro_unit.get_shutter_state()))
        
    def change_NLcorr_state(self):
        state=not(self.spectro_unit.device.get_nonlinearity_correction_usage())
        self.spectro_unit.device.set_nonlinearity_correction_usage(state)
    
    def change_EDcorr_state(self):
        state=not(self.spectro_unit.device.get_electric_dark_correction_usage())
        self.spectro_unit.device.set_electric_dark_correction_usage(state)
    
    def update_integration_time(self):
        t_ms=self.Tint.value()
        t_us=1000*t_ms #us
        self.spectro_unit.device.set_integration_time(t_us)
        self.spectro_unit.t_int=t_ms
        self.spectro_unit.update_acquisition_delay()

    def update_averaging(self):
        a=self.avg.value()
        self.spectro_unit.device.set_scans_to_average(a)
        self.spectro_unit.averaging=a
        self.spectro_unit.update_acquisition_delay()

    def updateDefaultParameters(self):
        parser = ConfigParser()
        parser.read(self.ihm.app_default_settings)
        file = open(self.ihm.app_default_settings,'w')
        parser.set('spectrometry', 'model', str(self.spectro_unit.model))
        parser.set('spectrometry', 'tint', str(self.spectro_unit.t_int))
        parser.set('spectrometry', 'avg', str(self.spectro_unit.averaging))
        parser.write(file)
        file.close()

if __name__ == "__main__":
    logger = od_logger()
    od = OceanDirectAPI()
    device_count = od.find_usb_devices() #nb d'appareils détectés
    device_ids = od.get_device_ids()
    if device_ids!=[]:
        id=device_ids[0]
        try:
            spectro = od.open_device(id) #crée une instance de la classe Spectrometer
            adv = Sp.Advanced(spectro)
            spectroIsConnected=True
            print("Spectro connecté")
        except:
            spectro=None #on crée dans tous les cas un objet Spectrometer
            adv = None
            spectroIsConnected=False
            print("Ne peut pas se connecter au spectro numéro ", id)
            pass
    else:
        spectro=None #on crée dans tous les cas un objet Spectrometer
        adv = None #Sp.Advanced(spectro)
        spectroIsConnected=False
        print("Spectro non connecté")
    #print("Nombre d'appareils OceanDirect détectés : ", device_count)
    #print("ID spectros: ", device_ids)

    spectrometry_unit=Instrument(od, spectro)

    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = SpectraWindow(spectrometry_unit)
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
