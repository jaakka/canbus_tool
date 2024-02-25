void canbus_simulation()
{
  if(simulation)
  {
    //ID: 407 DATA: 0xFD 0x8 0xBF 0xFF 0xFF 0xFF 0xFF 0xFF
    Serial.print("ID: ");
    Serial.print(String(random(101), HEX)); // 
    Serial.print(" DATA: ");
    Serial.print("0x" + String(random(101), HEX));
    Serial.print(" ");
    Serial.print("0x" + String(random(101), HEX));
    Serial.print(" ");
    Serial.print("0x" + String(random(101), HEX));
    Serial.print(" ");
    Serial.print("0x" + String(random(101), HEX));
    Serial.print(" ");
    Serial.print("0x" + String(random(101), HEX));
    Serial.print(" ");
    Serial.print("0x" + String(random(101), HEX));
    Serial.print(" ");
    Serial.print("0x" + String(random(101), HEX));
    Serial.print(" ");
    Serial.println("0x" + String(random(101), HEX));
  }
}