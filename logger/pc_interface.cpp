#include "mcp2515.h"
#include "crc8.h"
#include <Arduino.h>

#define ASSERT_CONCAT_(a, b) a##b
#define ASSERT_CONCAT(a, b) ASSERT_CONCAT_(a, b)
#define COMPILE_TIME_ASSERT(e) enum { ASSERT_CONCAT(assert_line_, __LINE__) = 1/(!!(e)) }


typedef struct _serial_packet {
    // Sentinel value to establish sync
    byte sentinel_start;
    // Sequence number
    uint16_t sequence;
    // Little-endian CAN ID (16b)
    uint16_t can_id;
    // 0 or 1
    byte rtr;
    // 0 to 8
    byte length;
    byte data[8];
    byte crc8;
} serial_packet;

// Constants shared with the Python PC-side interface
const byte PACKET_SIZE = 16;
// How many sync packets comprise a sync frame?
const byte SYNC_PACKETS = 2;
const byte SENTINEL_VALUE = 0xAA;

// If you get an error here, make sure you've synchronized
// the definitions of the constants with the structure, and
// with the Python PC interface
COMPILE_TIME_ASSERT(PACKET_SIZE == sizeof(serial_packet));

// Tunable parameters in this module
// Number of data packets we send between sending sync frames
// Increase this for higher efficiency; decrease it
//  - to reduce resync latency
//  - if synchronization drift is a problem (frequent resyncs)
const byte sends_per_sync = 126;
// How many packets have we sent since last sync frame?
static byte sends_since_sync = sends_per_sync;

void upload_CAN_message(tCAN* msg) {
    static uint16_t sequence = 0;
    serial_packet packet;
    if (sends_since_sync == sends_per_sync) {
        memset(&packet, 0, PACKET_SIZE);
        sends_since_sync = 0;
        for (byte i = 0; i < SYNC_PACKETS; i++)
            Serial.write((byte*)&packet, PACKET_SIZE);
    }
    packet.sentinel_start = SENTINEL_VALUE;
    packet.sequence = sequence;
    packet.can_id = msg->id;
    packet.rtr = msg->header.rtr;
    packet.length = msg->header.length;
    memcpy(packet.data, msg->data, packet.length);
    packet.crc8 = crc8((byte*)&packet, PACKET_SIZE - 1);
    Serial.write((byte*)&packet, PACKET_SIZE);
    sends_since_sync++;
    sequence++;
    Serial.flush();
}
