"Programme principal de l'application"

import sys
from PyQt5.QtWidgets import QApplication

#Model View Presenter architecture
from subsystems.Instrument import Instrument #model
from windows.main_window import MainWindow  #view
#from graphic.windows.main_win import Ui_MainWindow  #view

from Application import Application #presenter

def main():
    """Lancement application"""
    qApp = QApplication(sys.argv)
    
    model=Instrument()
    view=MainWindow()
    #lien entre les éléments graphiques et l'application et l'instrument
    app=Application(model,view) 

    view.show()
    sys.exit(qApp.exec_())

if __name__=='__main__':
    main()