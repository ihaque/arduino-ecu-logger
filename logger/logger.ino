/* Welcome to the ECU Reader project. This sketch uses the Canbus library.
It requires the CAN-bus shield for the Arduino. This shield contains the MCP2515 CAN controller and the MCP2551 CAN-bus driver.
A connector for an EM406 GPS receiver and an uSDcard holder with 3v level convertor for use in data logging applications.
The output data can be displayed on a serial LCD.

The SD test functions requires a FAT16 formated card with a text file of WRITE00.TXT in the card.


SK Pang Electronics www.skpang.co.uk
v4.0 04-03-12 Updated for Arduino 1.0
v3.0 21-02-11  Use library from Adafruit for sd card instead.

*/

#include <SD.h>
#include <SoftwareSerial.h>
#include "defaults.h"
#include "Canbus.h"
extern CanbusClass Canbus;

SoftwareSerial sLCD =  SoftwareSerial(0, CAN_BUS_LCD_TX); 
#define COMMAND 0xFE
#define CLEAR   0x01
#define LINE0   0x80
#define LINE1   0xC0


char buffer[128];  //Data will be temporarily stored to this buffer before being written to the file

int LED2 = 8;
int LED3 = 7;

// store error strings in flash to save RAM
#define error(s) error_P(PSTR(s))

void error_P(const char* str) {
    PgmPrint("error: ");
    SerialPrintln_P(str);
    Serial.println(str);
    
    clear_lcd();
    sLCD.print("SD error");
  
    while(1);
}

void initJoy(void) {
    pinMode(UP, INPUT_PULLUP);
    pinMode(DOWN, INPUT_PULLUP);
    pinMode(LEFT, INPUT_PULLUP);
    pinMode(RIGHT, INPUT_PULLUP);
    pinMode(CLICK, INPUT_PULLUP);
    return;
}

void initSD() {
  pinMode(CAN_BUS_SD_CS, OUTPUT);
  if (!SD.begin(CAN_BUS_SD_CS)) {
    Serial.println("SD initialization failed!");
    return;
  }
  Serial.println("SD initialization success");
  return;
}

void initLCD(unsigned int baud) {
  byte speed_control;
  switch (baud) {
    case 2400U: speed_control = 0x0B; break;
    case 4800U: speed_control = 0x0C; break;
    case 9600U: speed_control = 0x0D; break;
    case 14400U: speed_control = 0x0E; break;
    case 19200U: speed_control = 0x0F; break;
    case 38400U: speed_control = 0x10; break;
    default: baud = 9600U; speed_control = 0x0D; break;
  }
  
  sLCD.begin(9600U);
  sLCD.write(0x7C);
  sLCD.write(speed_control);
  delay(50); // Delay, or else LCD goes blank
  sLCD.begin(baud);
  return;
}

void setup() {
  Serial.begin(9600);
  pinMode(LED2, OUTPUT); 
  pinMode(LED3, OUTPUT); 
 
  digitalWrite(LED2, LOW);

  initJoy();
  initSD();
  initLCD(9600U);

  Serial.println("ECU Reader");  /* For debug use */
  
  clear_lcd();
 
  sLCD.print("D:CAN  U:GPS");
  sLCD.write(COMMAND);
  sLCD.write(LINE1); 
  sLCD.print("L:PIDs R:LOG");
  
  while(1)
  {
    
    if (digitalRead(UP) == 0){
      Serial.println("gps");
      sLCD.print("GPS");
    }
    
    if (digitalRead(DOWN) == 0) {
      sLCD.print("CAN");
      Serial.println("CAN");
      break;
    }
    
    if (digitalRead(LEFT) == 0) {
    
      Serial.println("PID dumper");
      dump_pids();
    }
    
    if (digitalRead(RIGHT) == 0) {
    
      Serial.println("Logging");
      logging();
    }
    
  }
  
  clear_lcd();
  
  if(Canbus.init(CANSPEED_500))  /* Initialise MCP2515 CAN controller at the specified speed */
  {
    sLCD.print("CAN Init ok");
  } else
  {
    sLCD.print("Can't init CAN");
  } 
   
  delay(1000); 

}
 

void loop() {
 
  if(Canbus.ecu_req(ENGINE_RPM,buffer) == 1)          /* Request for engine RPM */
  {
    sLCD.write(COMMAND);                   /* Move LCD cursor to line 0 */
    sLCD.write(LINE0);
    sLCD.print(buffer);                         /* Display data on LCD */
   
    
  } 
  digitalWrite(LED3, HIGH);
   
  if(Canbus.ecu_req(CALC_ENGINE_LOAD,buffer) == 1)
  {
    sLCD.write(COMMAND);
    sLCD.write(LINE0 + 9);
    sLCD.print(buffer);
   
  }
  
  if(Canbus.ecu_req(ENGINE_COOLANT_TEMP,buffer) == 1)
  {
    sLCD.write(COMMAND);
    sLCD.write(LINE1);                     /* Move LCD cursor to line 1 */
    sLCD.print(buffer);
   
   
  }
  
  if(Canbus.ecu_req(RELATIVE_THROTTLE,buffer) == 1)
  {
    sLCD.write(COMMAND);
    sLCD.write(LINE1 + 9);
    sLCD.print(buffer);
  }  
//  Canbus.ecu_req(O2_VOLTAGE,buffer);
     
   
   digitalWrite(LED3, LOW); 
   delay(100); 
   
   

}


void logging(void)
{
  clear_lcd();
  
  if(Canbus.init(CANSPEED_500))  /* Initialise MCP2515 CAN controller at the specified speed */
  {
    sLCD.print("CAN Init ok");
  } else
  {
    sLCD.print("Can't init CAN");
  } 
   
  delay(500);
  clear_lcd(); 
  sLCD.print("Init SD card");  
  delay(500);
  clear_lcd(); 
  sLCD.print("Press J/S click");  
  sLCD.write(COMMAND);
  sLCD.write(LINE1);                     /* Move LCD cursor to line 1 */
   sLCD.print("to Stop"); 
  
  // create a new file
  /*char name[] = "WRITE00.TXT";
  for (uint8_t i = 0; i < 100; i++) {
    name[5] = i/10 + '0';
    name[6] = i%10 + '0';
    if (file.open(&root, name, O_CREAT | O_EXCL | O_WRITE)) break;
  }
  if (!file.isOpen()) error ("file.create");
  Serial.print("Writing to: ");
  Serial.println(name);
  // write header
  file.writeError = 0;
  file.print("READY....");
  file.println();*/  

  while(1)    /* Main logging loop */
  {
    if(Canbus.ecu_req(ENGINE_RPM,buffer) == 1)          /* Request for engine RPM */
      {
        sLCD.write(COMMAND);                   /* Move LCD cursor to line 0 */
        sLCD.write(LINE0);
        sLCD.print(buffer);                         /* Display data on LCD */
       // file.print(buffer);
       //  file.print(',');
    
      } 
      digitalWrite(LED3, HIGH);
   
      if(Canbus.ecu_req(VEHICLE_SPEED,buffer) == 1)
      {
        sLCD.write(COMMAND);
        sLCD.write(LINE0 + 9);
        sLCD.print(buffer);
        //file.print(buffer);
        //file.print(','); 
      }
      
      if(Canbus.ecu_req(ENGINE_COOLANT_TEMP,buffer) == 1)
      {
        sLCD.write(COMMAND);
        sLCD.write(LINE1);                     /* Move LCD cursor to line 1 */
        sLCD.print(buffer);
        // file.print(buffer);
       
      }
      
      if(Canbus.ecu_req(THROTTLE,buffer) == 1)
      {
        sLCD.write(COMMAND);
        sLCD.write(LINE1 + 9);
        sLCD.print(buffer);
        // file.print(buffer);
      }  
    //  Canbus.ecu_req(O2_VOLTAGE,buffer);
       //file.println();  
  
       digitalWrite(LED3, LOW); 
 
       if (digitalRead(CLICK) == 0){  /* Check for Click button */
           //file.close();
           Serial.println("Done");
           sLCD.write(COMMAND);
           sLCD.write(CLEAR);
     
           sLCD.print("DONE");
          while(1);
        }

  }
 
 
 
 
}
     

void dump_pids(void)
{
 clear_lcd(); 
 sLCD.print("SD test"); 
 File f = SD.open("/SDtest.txt", FILE_WRITE);
 f.write("Hello, world!");
 f.close();

  if(!Canbus.init(CANSPEED_500))  /* Initialise MCP2515 CAN controller at the specified speed */
  {
    sLCD.print("Can't init CAN");
    while (1);
  } 
  delay(500);

  char buf[9*7 + 1];
  buf[9*7] = 0;
  for (byte row = 0; row < 7; row++) {
    for (byte col = 0; col < 8; col++) {
            buf[row*9 + col] = '-';
    }
    buf[row*9 + 8] = '\n';
  }
  byte CODES[7] = {PID_SUPPORT_01_20,
                   PID_SUPPORT_21_40,
                   PID_SUPPORT_41_60,
                   PID_SUPPORT_61_80,
                   PID_SUPPORT_81_A0,
                   PID_SUPPORT_A1_C0,
                   PID_SUPPORT_C1_E0};

  clear_lcd();
  sLCD.write(COMMAND);
  sLCD.write(LINE0);
  sLCD.write("Reading...");
  sLCD.write(COMMAND);
  sLCD.write(LINE1);
  f = SD.open("/PIDS_SUP.RAW", FILE_WRITE);
  f.write("\n");
  f.write("Starting new read\n");
  f.flush();
  f.close();
  for (int i = 0; i < 7; i++) {
    if (!Canbus.ecu_req(CODES[i], buf + 9*i)) {
            sLCD.write("Done.");
            break;
    } else {
            sprintf(buffer,"%d",i);
            sLCD.write(buffer);
    }
    f = SD.open("/PIDS_SUP.RAW", FILE_WRITE);
    f.write("\n\r");
    f.write(buf);
    Serial.write(buf);
    f.close();
  }

 while(1);  /* Don't return */ 
    

}

void clear_lcd(void)
{
  sLCD.write(COMMAND);
  sLCD.write(CLEAR);
}
