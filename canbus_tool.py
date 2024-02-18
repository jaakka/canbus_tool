import serial.tools.list_ports
import serial
import time
import sys
from PySide6.QtWidgets import QProgressBar, QApplication, QMainWindow, QComboBox, QPushButton, QWidget, QVBoxLayout,QLabel,QFrame,QLineEdit
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap,QIcon
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(600,200,320,240)

        # Aseta taustaväri
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.darkGray)  # Voit vaihtaa taustavärin haluamaksesi
        self.setPalette(p)

        #self.button = QPushButton("TEST",self)
        #self.button.setGeometry(310,0,100,20)
        #self.button.clicked.connect(self.laite_loyty)
        
        self.label = QLabel(self)
        pixmap = QPixmap(str(os.path.dirname(os.path.abspath(__file__)))+"\canbustyokalu.jpg")
        self.label.setPixmap(pixmap)
        self.label.setGeometry(40, -30, pixmap.width(), pixmap.height())

        self.setWindowTitle("CanbusHaistelija v0.1")
        self.txt = QLabel("Etsitään tuettua laitetta... \nJärjestelmä käynnistyy kun laite löytyy.", self) #luodaan tekstielementti
        self.txt.setGeometry(10,170,300,40)
        self.txt.setStyleSheet("color: white;")

        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "leikattutopseli.png")))

        self.palkki = QProgressBar(self) 
        self.palkki.setValue(99)
        self.palkki.setGeometry(0,210,370,30)

        self.dropdown = QComboBox(self)  #
        self.dropdown.addItem("Valitse nopeus")
        self.dropdown.addItem("83K3BPS")
        self.dropdown.addItem("100KBPS")
        self.dropdown.addItem("500KBPS")
        self.dropdown.setGeometry(220,210,100,30)
        self.dropdown.hide()
        self.dropdown.currentIndexChanged.connect(self.nopeus_valittu)
        self.show()

        self.laite = -1
        self.mode = 0
        
        ohjelmakierto = QTimer(self)
        ohjelmakierto.timeout.connect(self.ohjelma_looppi)
        ohjelmakierto.start() #tän sisälle voi laittaa myös ajan

        QTimer.singleShot(1000, self.etsinta)
        
    def etsinta(self):
        laite_ehdokkaat = self.etsi_mahdolliset()
        if len(laite_ehdokkaat) > 0:
            for i in range(len(laite_ehdokkaat)):
                self.ser = serial.Serial(laite_ehdokkaat[i], baudrate=115200)
                time.sleep(1)  # Odota vastausta
                response = self.ser.readline().decode('utf-8').rstrip() 
                if "odottaa" in response:
                    self.laite = laite_ehdokkaat[i]
                    print("Laite loydetty!")
                    break
                print("Yhteys katkaistu porttiin "+str(laite_ehdokkaat[i]))
                self.ser.close() # jossei laitetta loydy katkaistaan yhteys
            if self.laite != -1:
                # ei tartte enää alottaa pitääs ollaself.ser = serial.Serial(self.laite, baudrate=115200) #aloitetaan yhteys
                print("Yhdistetään laitteeseen "+str(self.laite))
                self.txt.setText("Yhdistetty laitteeseen VäyläTyökalu v1 ("+str(self.laite)+") \n Valitse haluamasi väylän-nopeus:")
                self.dropdown.show()
                self.palkki.hide()
        else:
            print("Ei yhtään mahdollista laitetta.")
        if self.laite == -1:
            QTimer.singleShot(1000, self.etsinta)
        
    def etsi_mahdolliset(self):
        laitteet = []
        # Etsi sarjaportit
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            if 'Arduino' in desc:  # Tarkista, onko kyseessä Arduino
                laitteet.append(port) #lisätään mahdolliset portit listalle
        return laitteet

    def nopeus_valittu(self):
        self.dropdown.hide()
        try:
            while True:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8').rstrip()
                    #print(data)
                    if self.mode == 0 and "odottaa" in data:  # odottaa fail valmiina
                        select = int(self.dropdown.currentIndex())
                        if select == 2:
                            print("CAN_100KBPS valittiin")
                            self.ser.write(b'CAN_100KBPS')
                        elif select == 3:
                            print("CAN_500KBPS valittiin")
                            self.ser.write(b'CAN_500KBPS')
                        else:
                            print("CAN_83K3BPS valittiin")
                            self.ser.write(b'CAN_83K3BPS') 
                        self.mode = 1 #odotetaan että valitaan CAN_83K3BPS CAN_100KBPS tai CAN_500KBPS

                    elif self.mode == 1:
                        if "valmiina" in data:  # odottaa fail valmiina
                            self.mode = 2 #odotetaan että valitaan CAN_83K3BPS CAN_100KBPS tai CAN_500KBPS
                            print("Valmiina toimintaan")
                            self.paavalikko()
                            break
                        elif "fail" in data:
                            print("Määritys ei onnistunut")
                            self.virhekoodi("VäyläTyökalun määritys epäonnistui.")
                            self.mode = 3 #määritys epäonnistui
                            break
                    elif self.mode == 2:
                        saatu_data = data.split()
                        print(saatu_data)
        except:
            self.virhekoodi("Yhteys VäyläTyökaluun menetettiin.")

    def paavalikko(self):
        nopeus = self.dropdown.currentText()
        self.txt.setText("Yhdistetty: VäyläTyökalu v1 ("+str(self.laite)+")\n Väylänopeus:"+str(nopeus) + "\n Dataliikenteen realiaikainen nopeus: 0 Msg/s")
        self.txt.setGeometry(10,5,300,50)
        self.dropdown.hide()
        self.label.hide()

    def virhekoodi(self,virhekoodi):
        self.txt.setText("Tapahtui virhe! \n virhekoodi: "+str(virhekoodi))
        self.txt.setGeometry(10,5,300,50)
        self.dropdown.hide()
        self.label.hide()

    def ohjelma_looppi(self):
        if self.mode == 2:
            print("test")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())