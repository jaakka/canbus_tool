#include <mcp_can.h>
#include <SPI.h>
bool maaritetty = false;

const int SPI_CS_PIN = 10;
MCP_CAN CANB(SPI_CS_PIN);

void setup() 
{
  Serial.begin(115200);
  while (!Serial) {;}
}

void loop() 
{
  if(maaritetty == false)
  {
    Serial.println("odottaa");
    delay(500);

    if(Serial.available())
    {
      String viesti = Serial.readString();
      if(viesti.indexOf("CAN_83K3BPS") != -1)
      {
        while (CAN_OK != CANB.begin(CAN_83K3BPS))
        {
          Serial.println("fail"); 
          delay(500);  
        }
        Serial.println("valmiina");
        maaritetty = true;
      }      
      if(viesti.indexOf("CAN_100KBPS") != -1)
      {
        while (CAN_OK != CANB.begin(CAN_100KBPS))
        {
          Serial.println("fail"); 
          delay(500);  
        }
        Serial.println("valmiina");
        maaritetty = true;
      }    
      if(viesti.indexOf("CAN_500KBPS") != -1)
      {
        while (CAN_OK != CANB.begin(CAN_500KBPS))
        {
          Serial.println("fail"); 
          delay(500);  
        }
        Serial.println("valmiina");
        maaritetty = true;
      }    
      if(viesti.indexOf("makkara") != -1)
      {
        Serial.println("kariste"); // laitteen varmennus ohjelmalle
      }  
    }
  }
    else
  {

    if (Serial.available()) 
    { 
      String viesti = Serial.readStringUntil('\n'); 

      int pilkun_indeksi = viesti.indexOf(',');
      if (pilkun_indeksi != -1) 
      {
        String str_pid = viesti.substring(0, pilkun_indeksi); //etitään eka pilkku
        long hex_pid = strtol(str_pid.c_str(), NULL, 16); //muunnetaan str > hex muotoon

        long data[8]; 
        String loppudata = viesti.substring(pilkun_indeksi+1,viesti.length());
        Serial.println(loppudata);
        for (int i = 0; i < 8; i++)
        {
          pilkun_indeksi = loppudata.indexOf(','); //etsitään seuraava pilkku
          String str_data = loppudata.substring(0, pilkun_indeksi);
          long hex_data = strtol(str_data.c_str(), NULL, 16); //muunnetaan str > hex muotoon
          data[i] = hex_data;

          loppudata = loppudata.substring(pilkun_indeksi+1,loppudata.length()); //lyhennetään tutkittavaa
        }
      
        byte data_bytes[8];
        for (int i = 0; i < 8; i++) 
        {
          data_bytes[i] = static_cast<byte>(data[i]); //tätä pitää vielä testata
        }

        CANB.sendMsgBuf(hex_pid, 0, 8, data_bytes);
        
        Serial.print("id: ");
        Serial.print("0x");
        Serial.print(hex_pid,HEX);
        Serial.print(" data: ");
        for (int i = 0; i < 8; i++)
        {
          Serial.print("0x");
          Serial.print(data[i],HEX);
          Serial.print(" ");
        }
        //esimerkki koodi 0x5B4,0x04,0x31,0x03,0x08,0x07,0xFF,0xFF,0xFF josta eka on pid
      }
    }
    unsigned char len = 1;
    unsigned char buf[8];

    if(CAN_MSGAVAIL == CANB.checkReceive())            // check if data coming
    {
      CANB.readMsgBuf(&len, buf);    // read data,  len: data length, buf: data buf

      unsigned int canId = CANB.getCanId();

      Serial.print("ID: ");
      Serial.print(canId,HEX); 
      Serial.print(" DATA: ");
      for(int i = 0; i<len; i++)    // print the data
      {
        if (buf[i] < 0b10000000) Serial.print("0"); 
        if (buf[i] < 0b1000000) Serial.print("0"); 
        if (buf[i] < 0b100000) Serial.print("0"); 
        if (buf[i] < 0b10000) Serial.print("0"); 
        if (buf[i] < 0b1000) Serial.print("0"); 
        if (buf[i] < 0b100) Serial.print("0"); 
        if (buf[i] < 0b10) Serial.print("0"); 
          Serial.print(buf[i], BIN); 
          Serial.print(" ");
      }
      Serial.println();
    }
  }
} 