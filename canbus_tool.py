import serial.tools.list_ports
import serial
import time
import sys
from PySide6.QtWidgets import QProgressBar, QApplication, QMainWindow, QComboBox, QPushButton, QWidget, QVBoxLayout,QLabel,QFrame,QLineEdit
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap,QIcon, QColor, QPainter
import os
import threading
from functools import partial # tämä sallii että napin connect toiminnon yhteydessä voidaan antaa argumentti
from tkinter import filedialog #tiedostojen käsittelyyn
import json

test = 0
tyotila = 0
laitteen_portti = "COM3"
ser = serial
total_msg = 0
total_msg_top = 0
vaylanluku = True
tutkinta_kaynnissa = False

missa_muodossa = 0

nimike_lista = []
pid_lista = []
data_lista = []
data_update_lista = []

old_data1 = []
old_data2 = []
old_data3 = []
old_data4 = []

def etsi_pid(pid):
    for i in range(len(pid_lista)):
        if pid_lista[i] == pid:
            return i
    return -1

def lista_update(index,kohta,data):
    old_data4[index][kohta] = old_data3[index][kohta]
    old_data3[index][kohta] = old_data2[index][kohta]
    old_data2[index][kohta] = old_data1[index][kohta]
    old_data1[index][kohta] = data_lista[index][kohta]
    data_lista[index][kohta] = data
    #print("dataupdate index:"+str(index)+ " kohta:"+str(kohta)+" data:"+str(data))

devices = 0

def kasittele_data(pid,data):
    index = etsi_pid(pid)
    if index == -1:
        pid_lista.append(pid)
        global devices
        devices += 1
        nimike_lista.append("Laite"+str(devices))

        setdata = []
        for i in range(8):
            if len(data)>i:
                setdata.append(data[i])
            else:
                setdata.append(-1)
        
        data_lista.append(setdata)
        old_data1.append([-1,-1,-1,-1,-1,-1,-1,-1])
        old_data2.append([-1,-1,-1,-1,-1,-1,-1,-1])
        old_data3.append([-1,-1,-1,-1,-1,-1,-1,-1])
        old_data4.append([-1,-1,-1,-1,-1,-1,-1,-1])
        data_update_lista.append([False,False,False,False,False,False,False,False])
        #index = len(pid_lista)-1
    else:
        i=0
        while i < 8:
            if len(data)>i:
                
                if data_lista[index][i] == data[i]:
                    data_update_lista[index][i] = False # ei uutta dataa
                else:
                    lista_update(index,i,data[i])
                    data_update_lista[index][i] = True # uus data
            i+=1

class yksiloityikkuna(QMainWindow):
    def __init__(self,index):
        super().__init__()
        self.setGeometry(600,460,320,220)
        self.index = index
        self.setWindowTitle(str(nimike_lista[index])+" tarkkailu [pid 0x"+str(pid_lista[index])+"]")
        self.setWindowIcon(QIcon(str(os.path.dirname(os.path.abspath(__file__)))+"\images\device.png"))

        # Aseta taustaväri
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.darkGray) 
        self.setPalette(p)

        self.ruututxt = []

        for y in range(6):
            vaakarivi = []
            for x in range(8):

                if y == 0:
                    frame = QFrame(self)
                    frame.setFrameShape(QFrame.Box)  # Asetetaan laatikon tyyli
                    frame.setLineWidth(1)  
                    frame.setGeometry(40*x,100+20*y,40,21)
                    frame.setStyleSheet("background-color: lightgray;")
                    data_txt = QLabel(str(x+1),self) #
                    data_txt.setGeometry(40*x,100,40,21)
                else:
                    data_txt = QLabel("-",self) #
                    data_txt.setStyleSheet("background-color: white;")
                    data_txt.setGeometry(40*x,100+20*y,40,21)
                    vaakarivi.append(data_txt)

            if y != 0:
                self.ruututxt.append(vaakarivi)

            self.nimilaatikko = QLineEdit(self)
            self.nimilaatikko.setText(str(nimike_lista[index]))
            self.nimilaatikko.textChanged.connect(self.rename)
            self.nimilaatikko.setGeometry(40,40,100,20)

            self.nimitxt = QLabel("Laitteen nimi",self)
            self.nimitxt.setGeometry(40,20,100,20)

            self.nollaustxt = QLabel("Nollaa väliaikainen\n kerätty data",self)
            self.nollaustxt.setGeometry(200,0,100,40)

            self.nollausbtn = QPushButton("Nollaa",self)
            self.nollausbtn.clicked.connect(self.reset)
            self.nollausbtn.setGeometry(200,40,100,20)

        self.show()
        QTimer.singleShot(50, self.update_data_loop)
    
    def reset(self):
        global data_lista, data_update_lista, old_data1, old_data2, old_data3, old_data4 
        data_update_lista[self.index] = [False,False,False,False,False,False,False,False]
        data_lista[self.index] = [-1,-1,-1,-1,-1,-1,-1,-1]
        old_data1[self.index] = [-1,-1,-1,-1,-1,-1,-1,-1]
        old_data2[self.index] = [-1,-1,-1,-1,-1,-1,-1,-1]
        old_data3[self.index] = [-1,-1,-1,-1,-1,-1,-1,-1]
        old_data4[self.index] = [-1,-1,-1,-1,-1,-1,-1,-1]

    def rename(self):
        global nimike_lista 
        nimike_lista[self.index] = self.nimilaatikko.text()
        self.setWindowTitle(str(nimike_lista[self.index])+" tarkkailu [pid 0x"+str(pid_lista[self.index])+"]")
        
        
    def test_are_null(self,value:str):
        if value == "-1":
            return ""
        else:
            if missa_muodossa == 0:
                return value
            elif missa_muodossa == 1:
                return str(bin(int(value, 16)))
            else:
                return str(int(value, 16))

    def update_data_loop(self):
        if len(data_update_lista)>self.index: # korjaa virheen kun nollaus painike sulkee seikkailu ikkunan
            if data_update_lista[self.index][0]:
                self.ruututxt[0][0].setStyleSheet("background-color: lime;")
            else:
                self.ruututxt[0][0].setStyleSheet("background-color: white;")
        
            if data_update_lista[self.index][1]:
                self.ruututxt[0][1].setStyleSheet("background-color: lime;")
            else:
                self.ruututxt[0][1].setStyleSheet("background-color: white;")

            if data_update_lista[self.index][2]:
                self.ruututxt[0][2].setStyleSheet("background-color: lime;")
            else:
                self.ruututxt[0][2].setStyleSheet("background-color: white;")

            if data_update_lista[self.index][3]:
                self.ruututxt[0][3].setStyleSheet("background-color: lime;")
            else:
                self.ruututxt[0][3].setStyleSheet("background-color: white;")

            if data_update_lista[self.index][4]:
                self.ruututxt[0][4].setStyleSheet("background-color: lime;")
            else:
                self.ruututxt[0][4].setStyleSheet("background-color: white;")

            if data_update_lista[self.index][5]:
                self.ruututxt[0][5].setStyleSheet("background-color: lime;")
            else:
                self.ruututxt[0][5].setStyleSheet("background-color: white;")

            if data_update_lista[self.index][6]:
                self.ruututxt[0][6].setStyleSheet("background-color: lime;")
            else:
                self.ruututxt[0][6].setStyleSheet("background-color: white;")

            if data_update_lista[self.index][7]:
                self.ruututxt[0][7].setStyleSheet("background-color: lime;")
            else:
                self.ruututxt[0][7].setStyleSheet("background-color: white;")

            self.ruututxt[0][0].setText(self.test_are_null(str(data_lista[self.index][0])))
            self.ruututxt[0][1].setText(self.test_are_null(str(data_lista[self.index][1])))
            self.ruututxt[0][2].setText(self.test_are_null(str(data_lista[self.index][2])))
            self.ruututxt[0][3].setText(self.test_are_null(str(data_lista[self.index][3])))
            self.ruututxt[0][4].setText(self.test_are_null(str(data_lista[self.index][4])))
            self.ruututxt[0][5].setText(self.test_are_null(str(data_lista[self.index][5])))
            self.ruututxt[0][6].setText(self.test_are_null(str(data_lista[self.index][6])))
            self.ruututxt[0][7].setText(self.test_are_null(str(data_lista[self.index][7])))

            self.ruututxt[1][0].setText(self.test_are_null(str(old_data1[self.index][0])))
            self.ruututxt[1][1].setText(self.test_are_null(str(old_data1[self.index][1])))
            self.ruututxt[1][2].setText(self.test_are_null(str(old_data1[self.index][2])))
            self.ruututxt[1][3].setText(self.test_are_null(str(old_data1[self.index][3])))
            self.ruututxt[1][4].setText(self.test_are_null(str(old_data1[self.index][4])))
            self.ruututxt[1][5].setText(self.test_are_null(str(old_data1[self.index][5])))
            self.ruututxt[1][6].setText(self.test_are_null(str(old_data1[self.index][6])))
            self.ruututxt[1][7].setText(self.test_are_null(str(old_data1[self.index][7])))

            self.ruututxt[2][0].setText(self.test_are_null(str(old_data2[self.index][0])))
            self.ruututxt[2][1].setText(self.test_are_null(str(old_data2[self.index][1])))
            self.ruututxt[2][2].setText(self.test_are_null(str(old_data2[self.index][2])))
            self.ruututxt[2][3].setText(self.test_are_null(str(old_data2[self.index][3])))
            self.ruututxt[2][4].setText(self.test_are_null(str(old_data2[self.index][4])))
            self.ruututxt[2][5].setText(self.test_are_null(str(old_data2[self.index][5])))
            self.ruututxt[2][6].setText(self.test_are_null(str(old_data2[self.index][6])))
            self.ruututxt[2][7].setText(self.test_are_null(str(old_data2[self.index][7])))

            self.ruututxt[3][0].setText(self.test_are_null(str(old_data3[self.index][0])))
            self.ruututxt[3][1].setText(self.test_are_null(str(old_data3[self.index][1])))
            self.ruututxt[3][2].setText(self.test_are_null(str(old_data3[self.index][2])))
            self.ruututxt[3][3].setText(self.test_are_null(str(old_data3[self.index][3])))
            self.ruututxt[3][4].setText(self.test_are_null(str(old_data3[self.index][4])))
            self.ruututxt[3][5].setText(self.test_are_null(str(old_data3[self.index][5])))
            self.ruututxt[3][6].setText(self.test_are_null(str(old_data3[self.index][6])))
            self.ruututxt[3][7].setText(self.test_are_null(str(old_data3[self.index][7])))

            self.ruututxt[4][0].setText(self.test_are_null(str(old_data4[self.index][0])))
            self.ruututxt[4][1].setText(self.test_are_null(str(old_data4[self.index][1])))
            self.ruututxt[4][2].setText(self.test_are_null(str(old_data4[self.index][2])))
            self.ruututxt[4][3].setText(self.test_are_null(str(old_data4[self.index][3])))
            self.ruututxt[4][4].setText(self.test_are_null(str(old_data4[self.index][4])))
            self.ruututxt[4][5].setText(self.test_are_null(str(old_data4[self.index][5])))
            self.ruututxt[4][6].setText(self.test_are_null(str(old_data4[self.index][6])))
            self.ruututxt[4][7].setText(self.test_are_null(str(old_data4[self.index][7])))


        QTimer.singleShot(10, self.update_data_loop)

class Tutkinta(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(920,200,400,480)
        self.setWindowTitle("Datan tutkinta")
        self.setWindowIcon(QIcon(str(os.path.dirname(os.path.abspath(__file__)))+"\images\search.png"))
        # Aseta taustaväri
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.white)  # Voit vaihtaa taustavärin haluamaksesi
        self.setPalette(p)
        self.ruudut=[]

        
        otsikot = ["Nimi","Pid","1","2","3","4","5","6","7","8"]
        self.nimi_lista = []
        self.data_ruutu1 = []
        self.data_ruutu2 = []
        self.data_ruutu3 = []
        self.data_ruutu4 = []
        self.data_ruutu5 = []
        self.data_ruutu6 = []
        self.data_ruutu7 = []
        self.data_ruutu8 = []


        last_y = -1
        for x in range(10):

            frame = QFrame(self)
            frame.setFrameShape(QFrame.Box)  # Asetetaan laatikon tyyli
            frame.setLineWidth(1)  
            frame.setStyleSheet("background-color: lightgray;")
            frame.setGeometry(40*x,0,40,21)
            self.ruudut.append(frame)

            self.tutkinta_txt = QLabel(otsikot[x],self)
            self.tutkinta_txt.setGeometry(5+40*x,0,40,21)

            

            for y in range(len(pid_lista)):

                

                frame = QFrame(self)
                frame.setFrameShape(QFrame.Box)  # Asetetaan laatikon tyyli
                frame.setLineWidth(1)  
                #frame.setStyleSheet("background-color: lime; color:black;")
                frame.setGeometry(40*x,20+20*y,40,21)

                self.ruudut.append(frame)

                if last_y != y and x == 0: # x estää ettei kerrota 10 :D  
                    #print("testaus:"+str(y))
                    #nämä ei käytännössä muutu joten tarvitsee piirtää kerran
                    self.tutkinta_txt = QLabel("0x"+str(pid_lista[(y)]),self)
                    self.tutkinta_txt.setGeometry(45,20+20*y,40,21)

                    #nämä taas muuttuu todennäköisesti joten lisätään listalle elementit että päästään myöhemmin käsiks
                    #nimi_txt = QLabel(str(nimike_lista[(y)]),self) #
                    nimi_txt = QPushButton(str(nimike_lista[(y)]),self)
                    nimi_txt.clicked.connect(partial(self.tutki_laitetta, y))
                    
                    nimi_txt.setGeometry(3,20+20*y,40,21)
                    self.nimi_lista.append(nimi_txt)

                    data_txt = QLabel(self.test_are_null(str(data_lista[(y)][0])),self) #
                    data_txt.setGeometry(82,20+20*y,40,21)
                    self.data_ruutu1.append(data_txt)

                    data_txt = QLabel(self.test_are_null(str(data_lista[(y)][1])),self) #str(data_lista[(y-1)][1])
                    data_txt.setGeometry(82+40,20+20*y,40,21)
                    self.data_ruutu2.append(data_txt)

                    data_txt = QLabel(self.test_are_null(str(data_lista[(y)][2])),self) #str(data_lista[(y-1)][2])
                    data_txt.setGeometry(82+40*2,20+20*y,40,21)
                    self.data_ruutu3.append(data_txt)

                    data_txt = QLabel(self.test_are_null(str(data_lista[(y)][3])),self) #str(data_lista[(y-1)][3])
                    data_txt.setGeometry(82+40*3,20+20*y,40,21)
                    self.data_ruutu4.append(data_txt)

                    data_txt = QLabel(self.test_are_null(str(data_lista[(y)][4])),self) #str(data_lista[(y-1)][4])
                    data_txt.setGeometry(82+40*4,20+20*y,40,21)
                    self.data_ruutu5.append(data_txt)

                    data_txt = QLabel(self.test_are_null(str(data_lista[(y)][5])),self) #str(data_lista[(y-1)][5])
                    data_txt.setGeometry(82+40*5,20+20*y,40,21)
                    self.data_ruutu6.append(data_txt)

                    data_txt = QLabel(self.test_are_null(str(data_lista[(y)][6])),self) #str(data_lista[(y-1)][6])
                    data_txt.setGeometry(82+40*6,20+20*y,40,21)
                    self.data_ruutu7.append(data_txt)

                    data_txt = QLabel(self.test_are_null(str(data_lista[(y)][7])),self) # str(data_lista[(y-1)][7])
                    data_txt.setGeometry(82+40*7,20+20*y,40,21)
                    self.data_ruutu8.append(data_txt)
                    
                    last_y = y #katotaan et kerran per kerros

                #frame.hide()
                
        QTimer.singleShot(100, self.update_data_loop)
        self.alaikkunat = []
        self.show()
    
    def test_are_null(self,value:str):
        if value == "-1":
            return ""
        else:
            if missa_muodossa == 0:
                return value
            elif missa_muodossa == 1:
                return str(bin(int(value, 16)))
            else:
                return str(int(value, 16))

    def tutki_laitetta(self,laite):
        print("Avataan laitetta indeksillä "+str(laite))
        self.alaikkunat.append(yksiloityikkuna(laite))

    def closeEvent(self, event):
        global tutkinta_kaynnissa
        tutkinta_kaynnissa = False

        
    def update_data_loop(self):
        if tutkinta_kaynnissa: #että ei suoriteta kun ikkuna suljettu, haamu toimintona 
            #print("nimike listan pituus "+str(len(self.nimi_lista)) + " / "+str(len(nimike_lista)))
            for i in range(len(self.nimi_lista)): #näitä pitäisi olla kaikkia sama määrä

                '''totalthings = len(self.nimi_lista) * 2 + 3
                if data_update_lista[i][0] == True:  
                    self.ruudut[totalthings].setStyleSheet("background-color: lime; color:black;")
                else:
                    self.ruudut[totalthings].setStyleSheet("background-color: white; color:black;")
                '''
                self.nimi_lista[i].setText(str(nimike_lista[i]))

                for b in range(8):
                    if len(data_update_lista)>i: #poistaa errorin kun ikkuna suljetaan nollaamisen takia
                        if data_update_lista[i][b]:
                            if b == 0:
                                self.data_ruutu1[i].setStyleSheet("background-color: lime;")
                            if b == 1:
                                self.data_ruutu2[i].setStyleSheet("background-color: lime;")
                            if b == 2:
                                self.data_ruutu3[i].setStyleSheet("background-color: lime;")
                            if b == 3:
                                self.data_ruutu4[i].setStyleSheet("background-color: lime;")
                            if b == 4:
                                self.data_ruutu5[i].setStyleSheet("background-color: lime;")
                            if b == 5:
                                self.data_ruutu6[i].setStyleSheet("background-color: lime;")
                            if b == 6:
                                self.data_ruutu7[i].setStyleSheet("background-color: lime;")
                            if b == 7:
                                self.data_ruutu8[i].setStyleSheet("background-color: lime;")
                        else:
                            if b == 0:
                                self.data_ruutu1[i].setStyleSheet("background-color: white;")
                            if b == 1:
                                self.data_ruutu2[i].setStyleSheet("background-color: white;")
                            if b == 2:
                                self.data_ruutu3[i].setStyleSheet("background-color: white;")
                            if b == 3:
                                self.data_ruutu4[i].setStyleSheet("background-color: white;")
                            if b == 4:
                                self.data_ruutu5[i].setStyleSheet("background-color: white;")
                            if b == 5:
                                self.data_ruutu6[i].setStyleSheet("background-color: white;")
                            if b == 6:
                                self.data_ruutu7[i].setStyleSheet("background-color: white;")
                            if b == 7:
                                self.data_ruutu8[i].setStyleSheet("background-color: white;")

                if len(data_lista) > i:
                    self.data_ruutu1[i].setText(self.test_are_null(str(data_lista[i][0])))
                    self.data_ruutu2[i].setText(self.test_are_null(str(data_lista[i][1])))
                    self.data_ruutu3[i].setText(self.test_are_null(str(data_lista[i][2])))
                    self.data_ruutu4[i].setText(self.test_are_null(str(data_lista[i][3])))
                    self.data_ruutu5[i].setText(self.test_are_null(str(data_lista[i][4])))
                    self.data_ruutu6[i].setText(self.test_are_null(str(data_lista[i][5])))
                    self.data_ruutu7[i].setText(self.test_are_null(str(data_lista[i][6])))
                    self.data_ruutu8[i].setText(self.test_are_null(str(data_lista[i][7])))



        QTimer.singleShot(100, self.update_data_loop)

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
        
        self.simu_txt = QLabel("Väylän simulointi",self)
        self.simu_txt.setGeometry(15,80,300,20)
        self.simu_txt.hide()

        self.btn_simu_on = QPushButton("Päälle",self)
        self.btn_simu_on.setGeometry(120,80,80,20)
        self.btn_simu_on.clicked.connect(self.simu_on)
        self.btn_simu_on.hide()

        self.btn_simu_off = QPushButton("Pois",self)
        self.btn_simu_off.setGeometry(210,80,80,20)
        self.btn_simu_off.clicked.connect(self.simu_off)
        self.btn_simu_off.hide()
        self.btn_simu_off.setDisabled(True)

        self.vayla_txt = QLabel("Väylän lukeminen",self)
        self.vayla_txt.setGeometry(15,110,300,20)
        self.vayla_txt.hide()

        self.btn_vayla_on = QPushButton("Päälle",self)
        self.btn_vayla_on.setGeometry(120,110,80,20)
        self.btn_vayla_on.clicked.connect(self.vayla_on)
        self.btn_vayla_on.setDisabled(True)
        self.btn_vayla_on.hide()

        self.btn_vayla_off = QPushButton("Pois",self)
        self.btn_vayla_off.setGeometry(210,110,80,20)
        self.btn_vayla_off.clicked.connect(self.vayla_off)
        self.btn_vayla_off.hide()

        self.nollaus_txt = QLabel("Luettu data",self)
        self.nollaus_txt.setGeometry(15,140,300,20)
        self.nollaus_txt.hide()

        self.btn_nollaus= QPushButton("Nollaa",self)
        self.btn_nollaus.setGeometry(210,140,80,20)
        self.btn_nollaus.clicked.connect(self.nollaus)
        self.btn_nollaus.hide()

        self.btn_tutkinta= QPushButton("Tutki",self)
        self.btn_tutkinta.setGeometry(120,140,80,20)
        self.btn_tutkinta.clicked.connect(self.aloita_tutkinta)
        self.btn_tutkinta.hide()

        self.tuonti_txt = QLabel("Laitteiden",self)
        self.tuonti_txt.setGeometry(15,170,300,20)
        self.tuonti_txt.hide()

        self.btn_avaa= QPushButton("Tuonti",self)
        self.btn_avaa.setGeometry(210,170,80,20)
        self.btn_avaa.clicked.connect(self.tuo)
        self.btn_avaa.hide()

        self.btn_tallenna= QPushButton("Vienti",self)
        self.btn_tallenna.setGeometry(120,170,80,20)
        self.btn_tallenna.clicked.connect(self.vie)
        self.btn_tallenna.hide()

        self.txt_aktiv = QLabel("Väylä ei aktiivinen",self)
        self.txt_aktiv.setStyleSheet("color:black; background-color:red; padding:2px;")
        self.txt_aktiv.setGeometry(10,210,100,20)
        self.txt_aktiv.hide()

        self.vaihda_txt = QLabel("Datan muoto",self)
        self.vaihda_txt.setGeometry(130,193,180,20)
        self.vaihda_txt.hide()

        self.btn_vaihda_hex= QPushButton("HEX",self)
        self.btn_vaihda_hex.setGeometry(130,210,60,20)
        self.btn_vaihda_hex.setDisabled(True)
        self.btn_vaihda_hex.clicked.connect(self.vaihda_hex)
        self.btn_vaihda_hex.hide()

        self.btn_vaihda_bin= QPushButton("BIN",self)
        self.btn_vaihda_bin.setGeometry(130+60,210,60,20)
        self.btn_vaihda_bin.clicked.connect(self.vaihda_bin)
        self.btn_vaihda_bin.hide()

        self.btn_vaihda_int= QPushButton("INT",self)
        self.btn_vaihda_int.setGeometry(130+60*2,210,60,20)
        self.btn_vaihda_int.clicked.connect(self.vaihda_int)
        self.btn_vaihda_int.hide()

        self.label = QLabel(self)
        pixmap = QPixmap(str(os.path.dirname(os.path.abspath(__file__)))+"\images\canbus_tool.jpg")
        self.label.setPixmap(pixmap)
        self.label.setGeometry(40, -30, pixmap.width(), pixmap.height())

        self.setWindowTitle("CanbusHaistelija v0.2")
        self.txt = QLabel("Etsitään tuettua laitetta... \nJärjestelmä käynnistyy kun laite löytyy.", self) #luodaan tekstielementti
        self.txt.setGeometry(10,170,300,40)
        self.txt.setStyleSheet("color: white;")

        self.setWindowIcon(QIcon(str(os.path.dirname(os.path.abspath(__file__)))+"\images\canbus_adapter.png"))

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
        

        self.laite = -1
        self.mode = 0
        '''
        self.nimilista=[]
        self.pidlista=[]
        self.datalista=[]
        
        
        
        for i in range(100):
            self.nimilista.append(QLabel(str("Tuntematon"), self)) #luodaan lempinimi lista
            self.nimilista[(len(self.nimilista)-1)].setGeometry(10,10 + 15 * i ,70,20)
            self.nimilista[(len(self.nimilista)-1)].hide()

            self.pidlista.append(QLabel(str("0x0"), self)) #luodaan pid lista
            self.pidlista[(len(self.pidlista)-1)].setGeometry(80,10 + 15 * i ,50,20)
            self.pidlista[(len(self.pidlista)-1)].hide()

            vaaka_lista = []
            for b in range(8):
                vaaka_lista.append(QLabel(str("0x0"), self)) #luodaan pid lista
                vaaka_lista[(len(vaaka_lista)-1)].setGeometry(80+40+25*b,10 + 15 * i ,30,20)
                vaaka_lista[(len(vaaka_lista)-1)].hide()

            self.datalista.append(vaaka_lista)'''

        self.show()
        
        #ohjelmakierto = QTimer(self)
        #ohjelmakierto.timeout.connect(self.ohjelma_looppi)
        #ohjelmakierto.start() #tän sisälle voi laittaa myös ajan
        
        QTimer.singleShot(1000, self.etsinta)

        QTimer.singleShot(1000, self.saako_avata_listan_loop)
    
    def tuo(self):
        global pid_lista, nimike_lista, data_lista, old_data1, old_data2, old_data3, old_data4, data_update_lista
        tiedostonimi = filedialog.askopenfilename(filetypes=[("Haistelijatiedostot", "*.haju")]) # Pyytää käyttäjää valitsemaan tiedoston
        if tiedostonimi:
            #tähän tulee tiedoston lukeminen
            f = open(str(tiedostonimi), "r")     #tiedoston avaus luku tilassa
            saatu_data = json.loads(f.read())            #tiedoston luku ja muunto str to array
            f.close() 
            if len(saatu_data) == 2:
                total_new_items = len(saatu_data[0]) # otetaan pid:it vastaan
                
                # jos lisätään laitteen jälkikäteen
                for i in range(total_new_items):
                    oli_jo_ind = -1

                    for a in range(len(pid_lista)):

                        if pid_lista[a] == saatu_data[0][i]:
                            oli_jo_ind = a

                    if oli_jo_ind == -1:

                        pid_lista.append(saatu_data[0][i]) 
                        nimike_lista.append(saatu_data[1][i])
                        data_lista.append([-1,-1,-1,-1,-1,-1,-1,-1])
                        old_data1.append([-1,-1,-1,-1,-1,-1,-1,-1])
                        old_data2.append([-1,-1,-1,-1,-1,-1,-1,-1])
                        old_data3.append([-1,-1,-1,-1,-1,-1,-1,-1])
                        old_data4.append([-1,-1,-1,-1,-1,-1,-1,-1])
                        data_update_lista.append([False,False,False,False,False,False,False,False])
                    else:
                        nimike_lista[oli_jo_ind] = saatu_data[1][i] #nimetään jo olemassa oleva pid listan mukaan
            else:
                print("Dataa ei ollut tai se oli väärässä muodossa.")
        else:
            print("Tuonti peruttiin")

    def vie(self):
        tiedostonimi = filedialog.asksaveasfilename(filetypes=[("Haistelijatiedostot", "*.haju")])
        if tiedostonimi:
            if ".haju" in tiedostonimi:
                pass
            else:
                tiedostonimi = str(tiedostonimi)+".haju" #tarkastetaan että tulee tiedostopääte

            f = open(str(tiedostonimi), "w")     #tiedoston avaus kirjoitus tilassa
            f.write(json.dumps([pid_lista,nimike_lista]))            #tiedoston kirjoitus ja muunto str to array
            f.close()    
        else:
            print("Vienti peruttiin")

    def vaihda_hex(self):
        global missa_muodossa
        missa_muodossa = 0
        self.btn_vaihda_hex.setDisabled(True)
        self.btn_vaihda_bin.setDisabled(False)
        self.btn_vaihda_int.setDisabled(False)
        print("Datan muoto vaihdettiin hex muotoon.")
    
    def vaihda_bin(self):
        global missa_muodossa
        missa_muodossa = 1
        self.btn_vaihda_bin.setDisabled(True)
        self.btn_vaihda_int.setDisabled(False)
        self.btn_vaihda_hex.setDisabled(False)
        print("Datan muoto vaihdettiin bin muotoon.")
    
    def vaihda_int(self):
        global missa_muodossa
        missa_muodossa = 2
        self.btn_vaihda_int.setDisabled(True)
        self.btn_vaihda_hex.setDisabled(False)
        self.btn_vaihda_bin.setDisabled(False)
        print("Datan muoto vaihdettiin int muotoon.")

    def saako_avata_listan_loop(self):
        if tutkinta_kaynnissa:
            self.btn_tutkinta.setDisabled(True)
        else:
            self.btn_tutkinta.setDisabled(False)
        QTimer.singleShot(1000, self.saako_avata_listan_loop)

    def aloita_tutkinta(self):
        global tutkinta_kaynnissa
        if tutkinta_kaynnissa == False:
            print("aloitetaan seikkailu ikkuna")
            self.tutkinta_ikkuna = Tutkinta()
            self.btn_tutkinta.setDisabled(True)

            tutkinta_kaynnissa = True

    def nollaus(self):
        global pid_lista 
        global data_lista 
        global data_update_lista 
        global old_data1 
        global old_data2 
        global old_data3 
        global old_data4 

        global tutkinta_kaynnissa #suljetaan ettei ikkuna yritä etsiä tyhjältä listalta
        if tutkinta_kaynnissa:
            self.tutkinta_ikkuna.close()
            tutkinta_kaynnissa = False

        pid_lista = []
        data_lista = []
        data_update_lista = []
        old_data1 = []
        old_data2 = []
        old_data3 = []
        old_data4 = []

        #jos tutkinta käynnissä ikkuna uudelleen avataan
        

    def vayla_on(self):
        print("Väylä painettu päälle")
        self.btn_vayla_on.setDisabled(True)
        self.btn_vayla_off.setDisabled(False)
        global vaylanluku
        vaylanluku = True

    def vayla_off(self):
        self.btn_vayla_off.setDisabled(True)
        self.btn_vayla_on.setDisabled(False)
        print("Väylä painettu pois päältä")
        global vaylanluku
        vaylanluku = False

    def aika_tekstin_paivittaja(self):
        nopeus = self.dropdown.currentText()
        self.txt.setText("Yhdistetty: VäyläTyökalu v1 ("+str(self.laite)+")\n Väylänopeus:"+str(nopeus) + "\n Dataliikenteen realiaikainen nopeus: "+str(total_msg_top)+" Msg/s \n Laitetunnisteita löytynyt: "+str(len(pid_lista))+"kpl")
        
        if total_msg_top>0:
            self.txt_aktiv.setText("Väylä aktiivinen")
            self.txt_aktiv.setStyleSheet("color:black; background-color:lime; padding:2px;")
        else:
            self.txt_aktiv.setText("Väylä ei aktiivinen")
            self.txt_aktiv.setStyleSheet("color:black; background-color:red; padding:2px;")

        QTimer.singleShot(100, self.aika_tekstin_paivittaja)

    def simu_on(self):
        print("Painettiin simulaattori päälle.")
        self.btn_simu_on.setDisabled(True)
        self.btn_simu_off.setDisabled(False)
        global tyotila
        tyotila = 1

    def simu_off(self):
        print("Painettiin simulaattori pois.")
        self.btn_simu_off.setDisabled(True)
        self.btn_simu_on.setDisabled(False)
        global tyotila
        tyotila = 2
        
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
        except Exception as koodi:
            self.virhekoodi("Yhteys VäyläTyökaluun menetettiin. \n")
            print("TarkempiVirhe:"+str(koodi))


    def paavalikko(self):
        nopeus = self.dropdown.currentText()
        self.txt.setText("Yhdistetty: VäyläTyökalu v1 ("+str(self.laite)+")\n Väylänopeus:"+str(nopeus) + "\n Dataliikenteen realiaikainen nopeus: 0 Msg/s \n Laitetunnisteita löytynyt: 0kpl")
        self.txt.setGeometry(10,5,300,65)
        self.dropdown.hide()
        self.label.hide()
        self.simu_txt.show()
        self.btn_simu_on.show()
        self.btn_simu_off.show()
        self.btn_vayla_on.show()
        self.btn_vayla_off.show()
        self.vayla_txt.show()
        self.btn_nollaus.show()
        self.nollaus_txt.show()
        self.btn_tutkinta.show()
        self.tuonti_txt.show()
        self.txt_aktiv.show()
        self.vaihda_txt.show()
        self.btn_vaihda_bin.show()
        self.btn_vaihda_hex.show()
        self.btn_vaihda_int.show()
        self.btn_avaa.show()
        self.btn_tallenna.show()
        #for i in range(len(self.ruudut)):
        #    for a in range(len(self.ruudut[i])):
        #        print(f"{i} - {a}")
        #        self.ruudut[i][a].show()

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
        if ikkuna_tehtava.is_alive() == False:
            print("Suljettiin ajanotto tehtävä koska ohjelman ikkuna suljettiin.")
            break 

        total_msg_top = total_msg
        total_msg = 0
        time.sleep(1)

def muunna_data(data):
    palautettava_data = []
    for i in range(len(data)):
        if i > 2: # ['(0)ID:', '(1)13', '(2)DATA:', '0x61', '0x4d', '0xc', '0x3b', '0x62', '0x49', '0x4c', '0x34']
            palautettava_data.append(data[i])
    return palautettava_data

def serial_teht():
    global total_msg
    global test
    global tyotila
    global ikkuna_tehtava
    global ser
    write_mode = False # tämä muuttettiin jos vaikuttaa että autoo ei lueta ennen kuin on simuloitu
    while True:

        if ikkuna_tehtava.is_alive() == False:
            print("Suljettiin datansiirto tehtävä koska ohjelman ikkuna suljettiin.")
            break 

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
                if vaylanluku:
                    saatu_data = data.split()
                    if len(saatu_data)>3:
                        kasittele_data(saatu_data[1], muunna_data(saatu_data))
                    #print(saatu_data)
        #print("työtila:"+str(tyotila))

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
    
    