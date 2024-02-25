#include <mcp_can.h>
#include <SPI.h>
bool maaritetty = false;
bool simulation = false;
const int SPI_CS_PIN = 10;
MCP_CAN CANB(SPI_CS_PIN);

// 57600 
void setup() 
{
  randomSeed(analogRead(0));
  Serial.begin(115200);
  while (!Serial) {;}
}

void loop() 
{
  if(maaritetty == false)
  {
    canbus_init(); //Määritetäään aloitusasetukset ohjelman kanssa
  }
    else
  {
    canbus_write(); //Kirjoittaa ohjelmalta saapuneen viestin väylään
    canbus_read(); //Lukee väylästä viestejä ja lähettää ohjelmalle
  }
  canbus_simulation();
}
