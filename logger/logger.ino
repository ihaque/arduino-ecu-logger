#include <SoftwareSerial.h>

#include "defaults.h"
#include "Canbus.h"
#include "mcp2515.h"
#include "pc_interface.h"
extern CanbusClass Canbus;

//#define FREE_MEMORY_MONITOR

SoftwareSerial sLCD =  SoftwareSerial(0, CAN_BUS_LCD_TX); 
#define COMMAND 0xFE
#define CLEAR   0x01
#define LINE0   0x80
#define LINE1   0xC0

// https://code.google.com/p/sdfatlib/
#include <SdFat.h>
#include <SdFile.h>

SdFat _sdfat;

// TODO store error strings in flash to save RAM
void error(const char* str) {
    Serial.print("error: ");
    Serial.println(str);
    
    clear_lcd();
    sLCD.print(str);
  
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
    if (!_sdfat.begin(CAN_BUS_SD_CS)) {
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

void initCAN() {
    // Initialize MCP2515 CAN controller at the specified speed
    if(Canbus.init(CANSPEED_500))
      sLCD.print("CAN Init ok");
    else {
      sLCD.print("Can't init CAN");
      while (1);
    }
    delay(500); 
}

void simulate_serial_dump(void) {
    tCAN msg;
    msg.id = 0x0001;
    msg.header.rtr = 0;
    msg.header.length = 8;
    msg.data[0] = 0x80;
    msg.data[1] = 0x08;
    msg.data[2] = 0x50;
    msg.data[3] = 0x00;
    msg.data[4] = 0xDE;
    msg.data[5] = 0xAD;
    msg.data[6] = 0xBE;
    msg.data[7] = 0xEF;
    clear_lcd();
    sLCD.write(COMMAND);
    sLCD.write(LINE0);
    sLCD.write("Simulating...");
    while (1) {
        upload_CAN_message(&msg);
        //msg.id = (msg.id * 907) % 23;
        //msg.data[3]++;
        //delay(5);
    }
}

void setup() {
    Serial.begin(250000);
    initJoy();
    initSD();
    initLCD(9600);
    clear_lcd();
    initCAN();

    Serial.println("ECU Reader");  /* For debug use */
  
    clear_lcd();

    sLCD.print("D:CAN  U:SPY");
    sLCD.write(COMMAND);
    sLCD.write(LINE1); 
    sLCD.print("L:PIDs R:SIM");
  
    while(1)
    {
        if (digitalRead(UP) == 0){
            Serial.println("can spy");
            sLCD.print("SPY");
            can_spy();
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
            Serial.println("Simulator");
            simulate_serial_dump();
        }
    }
  clear_lcd();
}
 
void loop() {
    char buffer[17];
    float mpg = compute_mpg();
    float oz_per_hr = consumption_ozph();
    sprintf(buffer,"%3u mpg %3u oz/h", (unsigned) mpg, (unsigned) oz_per_hr);
    sLCD.write(COMMAND);
    sLCD.write(LINE0);
    sLCD.write(buffer);
   
    //if(Canbus.ecu_req(CALC_ENGINE_LOAD,buffer) == 1) {
    //  sLCD.write(COMMAND);
    //  sLCD.write(LINE0 + 9);
    //  sLCD.print(buffer);
    //}
          
    if(Canbus.ecu_req(ENGINE_COOLANT_TEMP,buffer) == 1) {
        sLCD.write(COMMAND);
        sLCD.write(LINE1);
        sLCD.print(buffer);
    }
  
    if(Canbus.ecu_req(RELATIVE_THROTTLE,buffer) == 1) {
        sLCD.write(COMMAND);
        sLCD.write(LINE1 + 9);
        sLCD.print(buffer);
    }  
   
    delay(100); 
}

void logging(void) {
    char buffer[17];
    clear_lcd(); 
    sLCD.print("Press J/S click");  
    sLCD.write(COMMAND);
    sLCD.write(LINE1);                     /* Move LCD cursor to line 1 */
    sLCD.print("to Stop"); 
    
    while(1)    /* Main logging loop */
    {
        if(Canbus.ecu_req(ENGINE_RPM,buffer) == 1) {
            sLCD.write(COMMAND);
            sLCD.write(LINE0);
            sLCD.print(buffer);
            // file.print(buffer);
            //  file.print(',');
        } 
     
        if(Canbus.ecu_req(VEHICLE_SPEED,buffer) == 1) {
            sLCD.write(COMMAND);
            sLCD.write(LINE0 + 9);
            sLCD.print(buffer);
            //file.print(buffer);
            //file.print(','); 
        }
        
        if(Canbus.ecu_req(ENGINE_COOLANT_TEMP,buffer) == 1) {
            sLCD.write(COMMAND);
            sLCD.write(LINE1);
            sLCD.print(buffer);
            // file.print(buffer);
        }
        
        if(Canbus.ecu_req(THROTTLE,buffer) == 1) {
            sLCD.write(COMMAND);
            sLCD.write(LINE1 + 9);
            sLCD.print(buffer);
            // file.print(buffer);
        }  
        
        if (digitalRead(CLICK) == 0) {
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
    char buffer[17];
    clear_lcd(); 
    sLCD.print("SD test"); 
    SdFile fp;
    fp.open("SDtest.txt", O_WRITE | O_TRUNC);
    fp.write("Hello, world!");
    fp.close();
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
    fp.open("PIDS_SUP.RAW", O_WRITE | O_APPEND);
    fp.write("\n");
    fp.write("Starting new read\n");
    fp.sync();
    for (int i = 0; i < 7; i++) {
        if (!Canbus.ecu_req(CODES[i], buf + 9*i)) {
            sLCD.write("Done.");
            break;
        } else {
            sprintf(buffer,"%d",i);
            sLCD.write(buffer);
        }
        fp.write("\n\r");
        fp.write(buf);
        fp.sync();
    }
    fp.close();
   
    while(1);  /* Don't return */ 
}

bool get_CAN_msg(tCAN *pmsg, unsigned timeout_ms) {
    unsigned long start = millis();
    while (!mcp2515_check_message()) {
        if ((millis() - start) > timeout_ms) return false;
    }
    mcp2515_get_message(pmsg);
    return true;
}

void can_spy(void) {
    tCAN msg;
    unsigned long start = millis();
    int msg_count = 0;
    // 10fps
    const int update_period = 100;
    const int updates_per_sec = 1000 / update_period;
    unsigned long last_update = start - update_period;
    char buf[17];
    start_spy:
    #ifdef FREE_MEMORY_MONITOR
    freeMemory();
    #endif
    clear_lcd();
    sLCD.write(COMMAND);
    sLCD.write(LINE0);
    sLCD.print("Messages/sec:");
    while (get_CAN_msg(&msg, 10000U)) {
        msg_count++;
        upload_CAN_message(&msg);
        unsigned long tdelta = millis() - last_update;
        if (tdelta > update_period) {
            sLCD.write(COMMAND);
            sLCD.write(LINE1);
            // TODO: the timing here is not correct
            sprintf(buf, "%d", (int) (msg_count / (tdelta / 1000.0)));
            sLCD.print(buf);
            msg_count = 0;
            last_update = millis();
        }
    }
    sLCD.write(COMMAND);
    sLCD.write(LINE1);
    sLCD.print("None in 10 sec");
    while (1) {
      if (digitalRead(CLICK) == 0) goto start_spy;
    }
}

float compute_mpg(void) {
    /* VEHICLE_SPEED gives us speed in kph
     * MAF_SENSOR / 100 gives us gram/s air intake
     * O2_LAMBDA / 2^15 gives us ratio by which we are lean of stoich
     *
     * g air/s  * 1/14.7 g gas/g air / lambda = g gas/sec
     * g gas/s * 1 lb/454 g * 1 gal/6.701 lb * 3600 s/hr = gal gas/hr
     * speed kph * .621317 = speed mph
     * speed mph / gal gas/hr = mi/gal
     *
     * SPEED * 0.621317 * 14.7 * 454 * 6.701 * LAMBDA / (MAF * 3600) = mpg
     * SPEED * 27786 * LAMBDA / (MAF * 3600) = mpg
     * SPEED * 7.71833 * LAMBDA / (MAF) = mpg
     *
     * MAF_SENSOR = MAF * 100
     * O2_LAMBDA = LAMBDA * 32768
     *
     * SPEED * 7.71833 * O2_LAMBDA / 32768 / (MAF_SENSOR / 100) = mpg
     * SPEED * 7.71833 * O2_LAMBDA * 100 / (MAF_SENSOR * 32768) = mpg
     * SPEED * O2_LAMBDA / (MAF_SENSOR * 42.45478) = mpg
     */
    tOBD2 data;
    byte speed;
    unsigned maf_times_100, lambda_times_32k;
    float mpg;
    Canbus.obd2_data(VEHICLE_SPEED, &data);
    speed = data.A;
    Canbus.obd2_data(MAF_SENSOR, &data);
    maf_times_100 = ((unsigned)data.A << 8) | data.B;
    Canbus.obd2_data(O2_S1_WR_LAMBDA, &data);
    lambda_times_32k = ((unsigned)data.A << 8) | data.B;
    mpg = (float(speed) * lambda_times_32k) / (maf_times_100 * 42.45478);
    if (speed == 0) return 0.0f;
    else return mpg;
}

float consumption_ozph(void) {
    /* MAF_SENSOR / 100 gives us gram/s air intake
     * O2_S1_WR_LAMBDA / 2^15 gives us ratio by which we are lean of stoich
     *
     * g air/s  * 1/14.7 g gas/g air / lambda = g gas/sec
     * g gas/s * 1 lb/454 g * 1 gal/6.701 lb * 3600 s/hr  * 128 oz/gal = oz gas/hr
     *
     * (MAF_SENSOR / 100) * (1/14.7) / (O2_LAMBDA / 32768) * (1/454) * (1/6.701) * 3600 * 128
     * MAF_SENSOR * 32768 * 3600 * 128 / (100 * 14.7 * O2_LAMBDA * 454 * 6.701)
     *
     * MAF_SENSOR * 3376.36 / O2_LAMBDA = oz gas/hr
     */
    tOBD2 data;
    unsigned maf_times_100, lambda_times_32k;
    float oz_per_hr;
    Canbus.obd2_data(MAF_SENSOR, &data);
    maf_times_100 = ((unsigned)data.A << 8) | data.B;
    Canbus.obd2_data(O2_S1_WR_LAMBDA, &data);
    lambda_times_32k = ((unsigned)data.A << 8) | data.B;
    oz_per_hr = (maf_times_100 * 3376.36f) / lambda_times_32k;
    Serial.print("MAF = ");
    Serial.println(float(maf_times_100) / 100.0f);
    Serial.print("O2 LAMBDA =");
    Serial.println(float(lambda_times_32k) / 32768.0f);
    Serial.print("\n");
    return oz_per_hr;
}

void clear_lcd(void)
{
    sLCD.write(COMMAND);
    sLCD.write(CLEAR);
}

#ifdef FREE_MEMORY_MONITOR
extern unsigned int __heap_start;
extern void *__brkval;

/*
 * The free list structure as maintained by the 
 * avr-libc memory allocation routines.
 */
struct __freelist {
    size_t sz;
    struct __freelist *nx;
};

/* The head of the free list structure */
extern struct __freelist *__flp;

/* Calculates the size of the free list */
int freeListSize() {
    struct __freelist* current;
    int total = 0;

    for (current = __flp; current; current = current->nx) {
        total += 2; /* Add two bytes for the memory block's header  */
        total += (int) current->sz;
    }

    return total;
}

int freeMemory() {
    int free_memory;

    if ((int)__brkval == 0) {
        free_memory = ((int)&free_memory) - ((int)&__heap_start);
    } else {
        free_memory = ((int)&free_memory) - ((int)__brkval);
        free_memory += freeListSize();
    }
    sLCD.write(COMMAND);
    sLCD.write(LINE0);
    char _mbuf[12];
    sprintf(_mbuf, "%d b free", free_memory);
    sLCD.write(_mbuf);
    sLCD.write(COMMAND);
    sLCD.write(LINE1);
    sprintf(_mbuf, "%d b tCAN", sizeof(tCAN));
    sLCD.write(_mbuf);
    delay(1000);
    return free_memory;
}
#endif
