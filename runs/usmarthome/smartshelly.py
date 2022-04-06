#!/usr/bin/python3
from usmarthome.smartbase import Sbase, Slshelly
import subprocess


class Sshelly(Sbase):
    def __init__(self):
        # setting
        super().__init__()
        self._old_measuretype0 = 'none'
        print('__init__ Sshelly excuted')

    def getwatt(self, uberschuss, uberschussoffset):
        self.prewatt(uberschuss, uberschussoffset)
        self._mydevicemeasure0.devuberschuss = self.devuberschuss
        self._mydevicemeasure0.getwattread()
        self.newwatt = self._mydevicemeasure0.newwatt
        self.newwattk = self._mydevicemeasure0.newwattk
        self.relais = self._mydevicemeasure0.relais
        self.temp0 = self._mydevicemeasure0.temp0
        self.temp1 = self._mydevicemeasure0.temp1
        self.temp2 = self._mydevicemeasure0.temp2
        self.postwatt()

    def updatepar(self, input_param):
        super().updatepar(input_param)
        if (self._old_measuretype0 == 'none'):
            self._mydevicemeasure0 = Slshelly()
            self._old_measuretype0 = 'shelly'
            self.logClass(2, "(" + str(self.device_nummer) +
                          ") Integrierte Leistungsmessung. Neues Measure" +
                          " device erzeugt " + self.device_type)
        else:
            self.logClass(2, "(" + str(self.device_nummer) +
                          ") Integrierte Leistungsmessung. Nur Parameter " +
                          " update " + self.device_type)
        self._mydevicemeasure0.updatepar(input_param)

    def turndevicerelais(self, zustand, ueberschussberechnung, updatecnt):
        self.preturn(zustand, ueberschussberechnung, updatecnt)
        if (zustand == 1):
            pname = "/on.py"
        else:
            pname = "/off.py"

        argumentList = ['python3', self._prefixpy + 'shelly' + pname,
                        str(self.device_nummer), str(self._device_ip), '0']
        try:
            self.proc = subprocess.Popen(argumentList)
            self.proc.communicate()
        except Exception as e1:
            self.logClass(2, "(" + str(self.device_nummer) +
                          ") on / off %s %d %s Fehlermeldung: %s "
                          % ('Shelly', self.device_nummer,
                             str(self._device_ip), str(e1)))
