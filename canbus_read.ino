void canbus_read()
{
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