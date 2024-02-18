void canbus_write()
{
  if (Serial.available()) 
  { 
    String viesti = Serial.readStringUntil('\n'); 
    
    if(viesti.indexOf("makkara") != -1)
    {
      Serial.println("kariste"); // laitteen varmennus ohjelmalle
    }  
      else 
    {
      if(viesti.indexOf("simu_on") != -1)
      {
        simulation = true;
      } 
        else 
      {
        if(viesti.indexOf("simu_off") != -1)
        {
          simulation = false;
        }  
          else
        {
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
          }
        }
      }
    }
  }  
}

/* 

for debug
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

*/

//esimerkki koodi 0x5B4,0x04,0x31,0x03,0x08,0x07,0xFF,0xFF,0xFF josta eka on pid