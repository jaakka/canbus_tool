import serial.tools.list_ports
import serial
import time
import sys
from PySide6.QtWidgets import QProgressBar, QApplication, QMainWindow, QComboBox, QPushButton, QWidget, QVBoxLayout,QLabel,QFrame,QLineEdit
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap,QIcon
import os
import threading

test = 0
tyotila = 0
laitteen_portti = "COM3"
ser = serial
total_msg = 0
total_msg_top = 0

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
        #self.suomi_kentta.setStyleSheet("QLineEdit[readOnly=\"true\"] {"
              #"color: #585858;"
              #"background-color: #F0F0F0;"
              #"border: 1px solid #B0B0B0;}")
        
        self.simu_txt = QLabel("Aktivoi simulointi (ei vaikuta autoon)",self)
        self.simu_txt.setGeometry(15,70,300,40)
        self.simu_txt.hide()

        self.btn_simu_on = QPushButton("Päälle",self)
        self.btn_simu_on.setGeometry(10,100,100,20)
        self.btn_simu_on.clicked.connect(self.simu_on)
        self.btn_simu_on.hide()

        self.btn_simu_off = QPushButton("Pois",self)
        self.btn_simu_off.setGeometry(110,100,100,20)
        self.btn_simu_off.clicked.connect(self.simu_off)
        self.btn_simu_off.hide()
        self.btn_simu_off.setDisabled(True)
    

        self.label = QLabel(self)
        pixmap = QPixmap(str(os.path.dirname(os.path.abspath(__file__)))+"\canbus_tool.jpg")
        self.label.setPixmap(pixmap)
        self.label.setGeometry(40, -30, pixmap.width(), pixmap.height())

        self.setWindowTitle("CanbusHaistelija v0.1")
        self.txt = QLabel("Etsitään tuettua laitetta... \nJärjestelmä käynnistyy kun laite löytyy.", self) #luodaan tekstielementti
        self.txt.setGeometry(10,170,300,40)
        self.txt.setStyleSheet("color: white;")

        self.setWindowIcon(QIcon(str(os.path.dirname(os.path.abspath(__file__)))+"\canbus_adapter.png"))

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
        
        #ohjelmakierto = QTimer(self)
        #ohjelmakierto.timeout.connect(self.ohjelma_looppi)
        #ohjelmakierto.start() #tän sisälle voi laittaa myös ajan
        
        QTimer.singleShot(1000, self.etsinta)
    
    def aika_tekstin_paivittaja(self):
        nopeus = self.dropdown.currentText()
        self.txt.setText("Yhdistetty: VäyläTyökalu v1 ("+str(self.laite)+")\n Väylänopeus:"+str(nopeus) + "\n Dataliikenteen realiaikainen nopeus: "+str(total_msg_top)+" Msg/s")
        QTimer.singleShot(100, self.aika_tekstin_paivittaja)

    def simu_on(self):
        print("Painettiin simulaattori päälle.")
        self.btn_simu_on.setDisabled(True)
        self.btn_simu_off.setDisabled(False)
        global tyotila
        tyotila = 1
        print(tyotila)

    def simu_off(self):
        print("Painettiin simulaattori pois.")
        self.btn_simu_off.setDisabled(True)
        self.btn_simu_on.setDisabled(False)
        global tyotila
        tyotila = 2
        print(tyotila)
        
    def etsinta(self):
        global ser
        laite_ehdokkaat = self.etsi_mahdolliset()
        if len(laite_ehdokkaat) > 0:
            for i in range(len(laite_ehdokkaat)):
                ser = serial.Serial(laite_ehdokkaat[i], baudrate=115200)
                time.sleep(1)  # Odota vastausta
                response = ser.readline().decode('utf-8').rstrip() 
                if "odottaa" in response:
                    self.laite = laite_ehdokkaat[i]
                    global laitteen_portti
                    laitteen_portti = self.laite #asetetaan globaaliin muuttujaan laite
                    print("Laite loydetty!")
                    break
                print("Yhteys katkaistu porttiin "+str(laite_ehdokkaat[i]))
                ser.close() # yhteys katkeaa vain jossei laitetta loydy
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
        global ser
        try:
            while True:
                if ser.in_waiting > 0:
                    data = ser.readline().decode('utf-8').rstrip()
                    #print(data)
                    if self.mode == 0 and "odottaa" in data:  # odottaa fail valmiina
                        select = int(self.dropdown.currentIndex())
                        if select == 2:
                            print("CAN_100KBPS valittiin")
                            ser.write(b'CAN_100KBPS')
                            time.sleep(2)
                        elif select == 3:
                            print("CAN_500KBPS valittiin")
                            ser.write(b'CAN_500KBPS')
                            time.sleep(2)
                        else:
                            print("CAN_83K3BPS valittiin")
                            ser.write(b'CAN_83K3BPS')
                            time.sleep(2) 
                        self.mode = 1 #odotetaan että valitaan CAN_83K3BPS CAN_100KBPS tai CAN_500KBPS

                    elif self.mode == 1:
                        if "valmiina" in data:  # odottaa fail valmiina
                            self.mode = 2 #odotetaan että valitaan CAN_83K3BPS CAN_100KBPS tai CAN_500KBPS
                            print("Valmiina toimintaan")
                            #self.ser.close() #katkaistaan yhteys koska muodostetaan se uudelleen myöhemmin
                            self.paavalikko()
                            break
                        elif "fail" in data:
                            print("Määritys ei onnistunut")
                            self.virhekoodi("VäyläTyökalun määritys epäonnistui.")
                            self.mode = 3 #määritys epäonnistui
                            break
        except:
            self.virhekoodi("Yhteys VäyläTyökaluun menetettiin.")


    def paavalikko(self):
        nopeus = self.dropdown.currentText()
        self.txt.setText("Yhdistetty: VäyläTyökalu v1 ("+str(self.laite)+")\n Väylänopeus:"+str(nopeus) + "\n Dataliikenteen realiaikainen nopeus: 0 Msg/s")
        self.txt.setGeometry(10,5,300,50)
        self.dropdown.hide()
        self.label.hide()
        self.simu_txt.show()
        self.btn_simu_on.show()
        self.btn_simu_off.show()
        print("tyotila vaihtua 3")
        global tyotila
        tyotila = 3
        QTimer.singleShot(100, self.aika_tekstin_paivittaja)
        

    def virhekoodi(self,virhekoodi):
        self.txt.setText("Tapahtui virhe! \n virhekoodi: "+str(virhekoodi))
        self.txt.setGeometry(10,5,300,50)
        self.dropdown.hide()
        self.label.hide()

    def ohjelma_looppi(self):
        if self.mode == 2:
            print("test")


def ikkuna_teht():
    print("tehtava ikkuna aloitettiin")
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())



def aika_loop():
    global total_msg
    global total_msg_top
    while True:
        total_msg_top = total_msg
        total_msg = 0
        time.sleep(1)

def serial_teht():
    global total_msg
    global test
    global tyotila
    global ikkuna_tehtava
    global ser
    write_mode = True
    while True:

        #print("tyotila "+str(tyotila))

        if tyotila == 1: #simulaattori päälle
            i = 3
            write_mode = True
            while i > 0:
                ser.write(b'simu_on')
                time.sleep(1)
                i-=1
            print("Pyydettiin simulaattoria käynistymään")
            tyotila = 3
            write_mode = False

        if tyotila == 2: #simulaattori poispäältä                   
            i = 3
            write_mode = True
            while i > 0:
                ser.write(b'simu_off')
                time.sleep(1)
                i-=1
            print("Pyydettiin simulaattoria sammumaan")
            tyotila = 3
            write_mode = False

        if tyotila == 3 and write_mode == False: #väylän luku täysiä
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').rstrip()
                total_msg+=1
                saatu_data = data.split()
                print(saatu_data)

if __name__ == "__main__":
    ikkuna_tehtava = threading.Thread(target=ikkuna_teht, name='t1')
    serial_tehtava = threading.Thread(target=serial_teht, name='t2')
    aika_tehtava = threading.Thread(target=aika_loop, name='t3')

    ikkuna_tehtava.start()
    serial_tehtava.start()
    aika_tehtava.start()

    aika_tehtava.join()
    ikkuna_tehtava.join()
    serial_tehtava.join()
    
    print("Kaikki säikeet lopetettu.")
    
    