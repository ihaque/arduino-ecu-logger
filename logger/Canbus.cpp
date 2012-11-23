/**
 * 
 *
 * Copyright (c) 2008-2009  All rights reserved.
 */

#if ARDUINO>=100
#include <Arduino.h> // Arduino 1.0
#else
#include <Wprogram.h> // Arduino 0022
#endif
#include <stdint.h>
#include <avr/pgmspace.h>

#include <stdio.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include "pins_arduino.h"
#include <inttypes.h>
#include "global.h"
#include "mcp2515.h"
#include "defaults.h"
#include "Canbus.h"




/* C++ wrapper */
CanbusClass::CanbusClass() {

 
}
char CanbusClass::message_rx(unsigned char *buffer) {
		tCAN message;
	
		if (mcp2515_check_message()) {
		
			
			// Lese die Nachricht aus dem Puffern des MCP2515
			if (mcp2515_get_message(&message)) {
			//	print_can_message(&message);
			//	PRINT("\n");
				buffer[0] = message.data[0];
				buffer[1] = message.data[1];
				buffer[2] = message.data[2];
				buffer[3] = message.data[3];
				buffer[4] = message.data[4];
				buffer[5] = message.data[5];
				buffer[6] = message.data[6];
				buffer[7] = message.data[7];								
//				buffer[] = message[];
//				buffer[] = message[];
//				buffer[] = message[];
//				buffer[] = message[];																												
			}
			else {
			//	PRINT("Kann die Nachricht nicht auslesen\n\n");
			}
		}

}

char CanbusClass::message_tx(void) {
	tCAN message;


	// einige Testwerte
	message.id = 0x7DF;
	message.header.rtr = 0;
	message.header.length = 8;
	message.data[0] = 0x02;
	message.data[1] = 0x01;
	message.data[2] = 0x05;
	message.data[3] = 0x00;
	message.data[4] = 0x00;
	message.data[5] = 0x00;
	message.data[6] = 0x00;
	message.data[7] = 0x00;						
	
	
	
	
//	mcp2515_bit_modify(CANCTRL, (1<<REQOP2)|(1<<REQOP1)|(1<<REQOP0), (1<<REQOP1));	
		mcp2515_bit_modify(CANCTRL, (1<<REQOP2)|(1<<REQOP1)|(1<<REQOP0), 0);
		
	if (mcp2515_send_message(&message)) {
		return 1;
	
	}
	else {
	//	PRINT("Fehler: konnte die Nachricht nicht auslesen\n\n");
	return 0;
	}
return 1;
 
}

char CanbusClass::ecu_req(unsigned char pid,  char *buffer) 
{
    tOBD2 data;
    unsigned u16_eng_data = 0;
    
    if (obd2_data(pid, &data)) {
        switch(data.pid) {
            case ENGINE_RPM: // (A*256 + B)/4 RPM
                u16_eng_data = data.A;
                u16_eng_data <<= 8;
                u16_eng_data |= data.B;
                u16_eng_data >>= 4;
                if (data.B & 0x02) u16_eng_data++;
                sprintf(buffer, "%u rpm", u16_eng_data);
                break;
            
            case ENGINE_COOLANT_TEMP: // A-40 degC
                sprintf(buffer, "%u degC", (unsigned)(data.A - 40U));
                break;
            
            case VEHICLE_SPEED: // A kph
                sprintf(buffer, "%u kph", (unsigned) data.A);
                break;
            
            case MAF_SENSOR: //((256*A)+B)/100 g/s
                u16_eng_data = data.A;
                u16_eng_data = ((u16_eng_data << 8) | data.B) / 100U;
                sprintf(buffer, "%u g/s", u16_eng_data);
                break;

            case THROTTLE:
            case RELATIVE_THROTTLE:
            case CALC_ENGINE_LOAD: // A * 100 / 255
                u16_eng_data = data.A;
                u16_eng_data = (u16_eng_data * 100U) / 255U;
                sprintf(buffer, "%u %%", u16_eng_data);
                break;

            case PID_SUPPORT_01_20:
            case PID_SUPPORT_21_40:
            case PID_SUPPORT_41_60:
            case PID_SUPPORT_61_80:
            case PID_SUPPORT_81_A0:
            case PID_SUPPORT_A1_C0:
            case PID_SUPPORT_C1_E0:
                byte2hex(data.A, buffer);
                byte2hex(data.B, buffer+2);
                byte2hex(data.C, buffer+4);
                byte2hex(data.D, buffer+6);
                break;
        }
        return 1;
    } else {
        return 0;
	}
}

char CanbusClass::obd2_data(unsigned char pid, tOBD2 *data)
{
	tCAN message;
	int timeout = 0;
	char message_ok = 0;

    // Set up request message
	message.id = PID_REQUEST;
	message.header.rtr = 0;
	message.header.length = 8;
	message.data[0] = 0x02;
	message.data[1] = 0x01;
	message.data[2] = pid;
	message.data[3] = message.data[4] = message.data[5] = 0x00;
    message.data[6] = message.data[7] = 0x00;

	mcp2515_bit_modify(CANCTRL, (1<<REQOP2)|(1<<REQOP1)|(1<<REQOP0), 0);
	mcp2515_send_message(&message);

    while (timeout < 4000) {
        timeout++;
        if (mcp2515_check_message()) {
            if (mcp2515_get_message(&message)) {
                // If it's not a reply, try again.
                if (message.id != PID_REPLY || message.data[2] != pid) continue;
                data->pid = message.data[2];
                data->A = message.data[3];
                data->B = message.data[4];
                data->C = message.data[5];
                data->D = message.data[6];
                return 1;
            }
        }
    }
    return 0;
}






char CanbusClass::init(unsigned char speed) {

  return mcp2515_init(speed);
 
}

CanbusClass Canbus;
