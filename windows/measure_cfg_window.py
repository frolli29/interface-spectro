from configparser import ConfigParser

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDialog
from graphic.windows.measure_cfg_win import Ui_measureConfig

from file_manager import Data

class MeasureConfigWindow(QDialog,Ui_measureConfig): #(object)
    
    def __init__(self, ihm, parent=None):
        super(MeasureConfigWindow,self).__init__(parent)
        self.setupUi(self)
        self.ihm=ihm

        self.parser = ConfigParser()
        self.parser.read(ihm.app_default_settings)

        #graphique
        #défaut
        self.V_init.setSpecialValueText("")
        self.dispense_mode.setCurrentText(self.ihm.dispense_mode)
        self.sequence_config_file.setText(self.ihm.sequence_config_file)
        self.fixed_delay_box.setValue(self.ihm.fixed_delay_sec)
        self.agitation_delay_box.setValue(self.ihm.mixing_delay_sec)
        #mise en gris
        self.grey_out_widgets()

        #connexions
        self.browse1.clicked.connect(self.browseConfigFile)
        self.saving_folder.setText(self.ihm.saving_folder)  #dossier de sauvegarde
        self.browse.clicked.connect(self.browsefolder)
        self.dialogbox.accepted.connect(self.updateSettings)
        self.dialogbox.accepted.connect(self.launchTitration)
        self.dispense_mode.currentTextChanged.connect(self.grey_out_widgets)

    def update_infos(self):
        if self.dispense_mode.currentText() == "from file": #Custom sequence
            #affichage des données pour la séquence auto
            self.infos = ("\nName of experiment : ",self.exp_name.toPlainText(),\
            "\nDescription : ",self.description.toPlainText(),\
            "\nPresence of atmosphere : ",self.atmosphere_box.currentText(),\
            "\nInitial volume (mL) : ", self.V_init.value(),\
            "\nFibers : ", str(self.ihm.fibers),\
            "\nFlowcell : ",str(self.ihm.flowcell),\
            "\nDispense mode : ","from file",\
            "\nSequence instructions file : ",self.sequence_config_file.text(),\
            "\nData saving folder : ",self.ihm.seq.saving_folder)
        else:   #Classic sequence
            self.infos = ("\nName of experiment : ",self.exp_name.toPlainText(),\
            "\nDescription : ",self.description.toPlainText(),\
            "\nSample in ambiant atmosphere : ",self.atmosphere_box.currentText(),\
            "\nDispense mode : ",self.dispense_mode.currentText(),\
            "\nFibers : ",str(self.ihm.fibers),\
            "\nFlowcell : ",str(self.ihm.flowcell),\
            "\nInitial volume (mL) : ", self.V_init.value(),\
            "\ninitial pH : ",self.ihm.seq.pH_start,\
            "\nfinal pH : ",self.ihm.seq.pH_end,\
            "\nNumber of measures : ",self.ihm.seq.N_mes,\
            "\nMixing time (seconds): ", self.ihm.seq.mixing_delay_sec,\
            "\nFlow time (seconds): ", self.ihm.seq.fixed_delay_sec,\
            "\nData saving folder : ",self.ihm.seq.saving_folder)

    def grey_out_widgets(self):
        if self.dispense_mode.currentText()=="from file":
            self.Nmes.setDisabled(True)
            self.pH_init.setDisabled(True)
            self.pH_fin.setDisabled(True)
            self.fixed_delay_box.setDisabled(True)
            self.agitation_delay_box.setDisabled(True)
            self.sequence_config_file.setDisabled(False) #chemin fichier de sequence
        else:
            self.Nmes.setDisabled(False)
            self.pH_init.setDisabled(False)
            self.pH_fin.setDisabled(False)
            self.fixed_delay_box.setDisabled(False)
            self.agitation_delay_box.setDisabled(False)
            self.sequence_config_file.setDisabled(True) #chemin du fichier de sequence

    def browsefolder(self):
        parser = ConfigParser()
        parser.read(self.ihm.app_default_settings)
        fld=parser.get('saving parameters', 'folder')  #affichage par défaut
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder', fld)
        self.saving_folder.setText(folderpath) #affichage du chemin de dossier
        self.ihm.saving_folder=self.saving_folder.text()
        #self.ihm.updateDefaultParam()
    
    def browseConfigFile(self):
        parser = ConfigParser()
        parser.read(self.ihm.app_default_settings)
        seq_file=self.parser.get('custom sequence', 'sequence_file')  #affichage par défaut à l'ouverture
        filepath, filter = QtWidgets.QFileDialog.getOpenFileName(self, 'Select File', seq_file, filter="*.csv")
        self.sequence_config_file.setText(filepath) #affichage du chemin de dossier
        self.ihm.sequence_config_file=filepath
    
    def launchTitration(self):
        
        if self.dispense_mode.currentText() == "from file": #sequence instruction file
            config = [self.exp_name.toPlainText(),self.description.toPlainText(),\
            bool(self.atmosphere_box.currentText()),str(self.ihm.fibers),\
            str(self.ihm.flowcell),self.V_init.value(),self.dispense_mode.currentText(),\
            self.sequence_config_file.text(),self.saving_folder.text()]
            self.ihm.seq=CustomSequence(self.ihm,config) #creation of object sequence
            self.ihm.seq_data=Data(self.ihm.seq)
            self.ihm.seq.configure()
            self.ihm.seq.run_sequence()
        else:   #classic sequence
            config = [self.exp_name.toPlainText(),self.description.toPlainText(),\
            bool(self.atmosphere_box.currentText()),str(self.ihm.fibers),str(self.ihm.flowcell),\
            self.V_init.value(),self.dispense_mode.currentText(),self.Nmes.value(),\
            self.pH_init.value(),self.pH_fin.value(),self.fixed_delay_box.value(),\
            self.agitation_delay_box.value(),self.saving_folder.text()]
            self.ihm.seq=ClassicSequence(self.ihm,config)
            self.ihm.seq_data=Data(self.ihm.seq)
            self.ihm.seq.configure()
        self.update_infos()
        print(self.infos)
    
    def updateSettings(self):
        self.ihm.dispense_mode=self.dispense_mode.currentText()
        self.ihm.fixed_delay_sec=int(self.fixed_delay_box.value())
        self.ihm.mixing_delay_sec=int(self.agitation_delay_box.value())
        
        parser = ConfigParser()
        parser.read(self.ihm.app_default_settings)
        parser.set('sequence','dispense_mode',self.dispense_mode.currentText())
        parser.set('custom sequence', 'sequence_file', self.sequence_config_file.text())
        parser.set('classic titration sequence', 'fixed_delay_sec', str(self.fixed_delay_box.value()))
        parser.set('classic titration sequence', 'mixing_delay_sec', str(self.agitation_delay_box.value()))
        parser.set('saving parameters','folder',self.saving_folder.text())
        
        file = open(self.ihm.app_default_settings,'r+')
        parser.write(file)
        file.close()

#Lancement direct du programme avec run
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ihm=IHM()
    win=WindowHandler()
    ui = MeasureConfigWindow(ihm,win)
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
