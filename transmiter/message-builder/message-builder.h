#ifndef MessageBuilder_h
#define MessageBuilder_h

#include "Arduino.h"

void buildMessage(byte* message, int buttonId, int buttonState, unsigned long timestamp) {
  message[0] = (byte)buttonId;
  message[1] = (byte)(timestamp >> 40);
  message[2] = (byte)(timestamp >> 32);
  message[3] = (byte)(timestamp >> 24);
  message[4] = (byte)(timestamp >> 16);
  message[5] = (byte)(timestamp >> 8);
  message[6] = (byte)timestamp;
  message[7] = (byte)buttonState;
  
  byte checksum = 0;
  for (int i = 0; i < 8; i++) {
    checksum += message[i];
  }
  message[8] = checksum;
}

#endif