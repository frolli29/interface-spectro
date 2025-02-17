"Classe System qui contient des fonctions système utilisant plusieurs instruments"

from Phidget22.Phidget import *
from Phidget22.Devices.DigitalOutput import *

from configparser import ConfigParser
import os
from pathlib import Path

path = Path(__file__)
ROOT_DIR = path.parent.parent.absolute() #répertoire pytitrator
app_default_settings = os.path.join(ROOT_DIR, "config/app_default_settings.ini")
device_ids = os.path.join(ROOT_DIR, "config/device_id.ini")

class System: 

        parser = ConfigParser()
        parser.read(device_ids)
        board_number = int(parser.get('main board', 'id'))
        VINT_number = int(parser.get('VINT', 'id'))

        digitalOutput_test = DigitalOutput()
        digitalOutput_test.setDeviceSerialNumber(board_number)
        def __init__(self):
                self.state='disconnected'
                sn=self.digitalOutput_test.getDeviceSerialNumber()
                print(sn)
                try:
                        self.digitalOutput_test.openWaitForAttachment(1000)
                except:
                        print("Board not powered or plugged")
                if self.digitalOutput_test.getIsOpen():
                        nb=self.digitalOutput_test.getDeviceSerialNumber()
                        name=self.digitalOutput_test.getDeviceClassName()
                        print("\nserial number : ",nb,"\nName : ", name)
                        self.state='connected'



if __name__=="__main__":
        system=System()
        print(system.state)