void canbus_init()
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