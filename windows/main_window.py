# main_window.py

from configparser import ConfigParser
import os

from PyQt5.QtWidgets import QMainWindow
from graphic.windows.main_win import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QObject

from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

from subsystems.Instrument import Instrument

from lib.oceandirect.OceanDirectAPI import Spectrometer as Sp, OceanDirectAPI
from lib.oceandirect.od_logger import od_logger

#chemin du repertoire _internal lors du lancement de l'exe
path_internal=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
green_led_path=os.path.join(path_internal, "graphic/images/green-led-on.png")
red_led_path=os.path.join(path_internal, "graphic/images/red-led-on.png")

from pathlib import Path
path = Path(__file__)
ROOT_DIR = path.parent.absolute()
settings = os.path.join(ROOT_DIR, "settings.ini")

"""class CustomSignals(QObject):
	co_disco=pyqtSignal()"""

class MainWindow(QMainWindow, Ui_MainWindow):

    #Signals must be defined in the class
    co_disco=pyqtSignal()
    #shutter=pyqtSignal()
    #signal_shutter=
    window_close=pyqtSignal()

    def __init__(self, parent=None):
        #graphique
        super(MainWindow,self).__init__(parent)
        self.setupUi(self)
        
        if os.path.exists(green_led_path):  #lors d'un lancement avec le dossier d'executable
            self.pixmap_green=QtGui.QPixmap(green_led_path)
            self.pixmap_red=QtGui.QPixmap(red_led_path)
        else:
            self.pixmap_green=QtGui.QPixmap("graphic/images/green-led-on.png")
            self.pixmap_red=QtGui.QPixmap("graphic/images/red-led-on.png")

        #Affichage
        self.state_light.setScaledContents(True)
        #Saving

        #Graphique pour les spectres
        (w,h)=(self.graphic_tabs.geometry().width(),self.graphic_tabs.geometry().height())
        rect=QtCore.QRect(0,0,w-5,h-32)
        self.Spectrum_direct = pg.PlotWidget(self.tab1)
        self.Spectrum_direct.setGeometry(rect)
        self.Spectrum_direct.setObjectName("Spectrum_direct")
        self.Abs_direct = pg.PlotWidget(self.tab2)
        self.Abs_direct.setGeometry(rect)
        self.Abs_direct.setObjectName("Abs_direct")
        
        self.intensity_direct_plot=self.Spectrum_direct.plot([0],[0])
        self.abs_direct_plot=self.Abs_direct.plot([0],[0])

        #self.app.timer_display.timeout.connect(self.refresh_screen)
        #self.close_all.clicked.connect(self.app.close_all_devices)
        #self.close_all.clicked.connect(self.clear_app)

    def display_saving_param(self,param):
        self.saving_folder.setText(param[0])
        self.intensity_box.setChecked(bool(param[1]))
        print(self.intensity_box.isChecked())
        self.absorbance_box.setChecked(bool(param[2]))
        self.transmittance_box.setChecked(bool(param[3]))
        self.N_spectra.setValue(int(param[4]))
        self.T_sec.setValue(float(param[5]))
        print(param)

    def display_connexion_state(self, state):
        """Updates light indicator and Connexion button"""
        if state=='closed':
            self.state_light.setPixmap(self.pixmap_red)
            self.connect_disconnect_spectro_button.setText("Connect")
        elif state=='open':
            self.state_light.setPixmap(self.pixmap_green)
            self.connect_disconnect_spectro_button.setText("Disconnect")

    def closeEvent(self, event):
        print("Closing main window")
        self.window_close.emit()