#include "mcp2515.h"
#include <Arduino.h>
// 12b packet sent on serial wire.
// Make sure syncLength is an integral multiple of that.
const byte syncLength  = 2*12;
const byte sends_per_sync = 127;
static byte sends_since_sync = sends_per_sync;

void upload_CAN_message(tCAN* msg) {
    /* Message format
     * 16b uint little-endian address 
     * 8b uint rtr
     * 8b uint length
     * 64b data
     */
    byte i;
    if (sends_since_sync == sends_per_sync) {
        sends_since_sync = 0;
        for (i = 0; i < syncLength; i++)
            Serial.write((uint8_t)0);
    }
    Serial.write((byte)(msg->id & 0xFF));
    Serial.write((byte)(msg->id >> 8));
    Serial.write((byte)(msg->header.rtr));
    Serial.write((byte)(msg->header.length));
    Serial.write(msg->data, 8);
    sends_since_sync++;
}
