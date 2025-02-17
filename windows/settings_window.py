"""classe pour dispenser_param"""

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog

from graphic.windows.settings_win import Ui_Dialog    #fenetre créée sur Qt designer

from configparser import ConfigParser

class SettingsWindow(QDialog,Ui_Dialog): #(object)
    
    def __init__(self, ihm, parent=None):
        super(SettingsWindow,self).__init__(parent)
        self.setupUi(self)
        self.ihm=ihm
        self.syringe_A=ihm.dispenser.syringe_A
        self.syringe_B=ihm.dispenser.syringe_B
        self.syringe_C=ihm.dispenser.syringe_C

        self.parser = ConfigParser()
        self.parser.read(ihm.app_default_settings)

        #Sauvegarde de la config
        self.buttonBox.accepted.connect(self.update)

        #consignes de dispense
        self.disp_A.clicked.connect(self.syringe_A.standard_dispense_for_calib)
        self.disp_B.clicked.connect(self.syringe_B.standard_dispense_for_calib)
        self.disp_C.clicked.connect(self.syringe_C.standard_dispense_for_calib)

        #calcul du rescale factor
        self.cal_A.clicked.connect(self.compute_rescale_factor_A)
        self.cal_B.clicked.connect(self.compute_rescale_factor_B)
        self.cal_C.clicked.connect(self.compute_rescale_factor_C)

        #affichage des paramètres courants
        self.offset_A.setValue(self.ihm.dispenser.syringe_A.offset_ref) #int
        self.offset_B.setValue(self.ihm.dispenser.syringe_B.offset_ref)
        self.offset_C.setValue(self.ihm.dispenser.syringe_C.offset_ref)
        self.syringeA.setChecked(self.ihm.dispenser.syringe_A.use)   #bool
        self.syringeB.setChecked(self.ihm.dispenser.syringe_B.use)
        self.syringeC.setChecked(self.ihm.dispenser.syringe_C.use)
        self.reagentA.setText(self.ihm.dispenser.syringe_A.reagent)   #string
        self.reagentB.setText(self.ihm.dispenser.syringe_B.reagent)
        self.reagentC.setText(self.ihm.dispenser.syringe_C.reagent)
        self.Ca.setValue(self.ihm.dispenser.syringe_A.concentration)  #float
        self.Cb.setValue(self.ihm.dispenser.syringe_B.concentration)
        self.Cc.setValue(self.ihm.dispenser.syringe_C.concentration)
        self.fibers.setCurrentText(self.ihm.fibers)
        self.flowcell.setCurrentText(self.ihm.flowcell)

        self.saving_folder.setText(self.ihm.saving_folder)
        self.browse.clicked.connect(self.browseSavingFolder)
    
    def dispense(self,id):
        if id=='A':
            self.ihm.dispenser.syringe_A.dispense(300)
        if id=='B':
            self.ihm.dispenser.syringe_B.dispense(300)
        if id=='C':
            self.ihm.dispenser.syringe_C.dispense(300)

    def compute_rescale_factor_A(self):
        self.syringe_A.compute_rescale_factor(self.reached_A_uL.value())

    def compute_rescale_factor_B(self):
        self.syringe_B.compute_rescale_factor(self.reached_B_uL.value())
    
    def compute_rescale_factor_C(self):
        self.syringe_C.compute_rescale_factor(self.reached_C_uL.value())
    
    def browseSavingFolder(self):
        fld=self.parser.get('saving parameters', 'folder')  #affichage par défaut
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder', fld)
        self.saving_folder.setText(folderpath) #affichage du chemin de dossier
        self.ihm.saving_folder=self.saving_folder.text()
        self.ihm.updateDefaultParam()

    def update(self):
        fibers = str(self.fibers.currentText())
        flowcell = str(self.flowcell.currentText())
        self.ihm.fibers=fibers
        self.ihm.flowcell=flowcell

        #update the default config file
        parser = ConfigParser()
        parser.read(self.ihm.app_default_settings)
        parser.set('Syringe A', 'offset_ref', str(self.offset_A.value()))
        parser.set('Syringe A', 'rescale_factor', str(self.syringe_A.rescale_factor))
        parser.set('Syringe A', 'use', str(self.syringeA.isChecked()))
        parser.set('Syringe A', 'reagent', str(self.reagentA.toPlainText()))
        parser.set('Syringe A', 'concentration', str(self.Ca.value()))
        parser.set('Syringe B', 'offset_ref', str(self.offset_B.value()))
        parser.set('Syringe B', 'rescale_factor', str(self.syringe_B.rescale_factor))
        parser.set('Syringe B', 'use', str(self.syringeB.isChecked()))
        parser.set('Syringe B', 'reagent', str(self.reagentB.toPlainText()))
        parser.set('Syringe B', 'concentration', str(self.Cb.value()))
        parser.set('Syringe C', 'offset_ref', str(self.offset_C.value()))
        parser.set('Syringe C', 'rescale_factor', str(self.syringe_C.rescale_factor))
        parser.set('Syringe C', 'use', str(self.syringeC.isChecked()))
        parser.set('Syringe C', 'reagent', str(self.reagentC.toPlainText()))
        parser.set('Syringe C', 'concentration', str(self.Cc.value()))
        parser.set('setup', 'fibers', fibers)
        parser.set('setup', 'flowcell', flowcell)
        file = open(self.ihm.app_default_settings,'w')
        parser.write(file)
        file.close()
        
        self.ihm.dispenser.update_param_from_file() #modif des attributs de la classe Dispenser

        print("Updating instruments parameters")