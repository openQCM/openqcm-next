/* LICENSE
 * Copyright (C) 2014 openQCM
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses/gpl-3.0.txt
 *
 * INTRO
 * Program for storing the openQCM NEXT machine identification number in the
 * Teensy EEPROM. Ported from openQCM_Q-1_SerialNumber v2.1 and following the
 * serial-number format specification, which the Q-1 and the NEXT share.
 *
 * Target: Teensy 4.0 (the board the NEXT mounts). The EEPROM layout is the one
 * the Q-1 uses, byte for byte, so a board programmed with either tool is read
 * correctly by both.
 *
 * EEPROM LAYOUT (4 bytes)
 *   Address 0: MAGIC byte (0xA5) -- flags that a serial number has been written
 *   Address 1: SERIES           -- production batch, 0-255
 *   Address 2: SERIAL HIGH      -- unit number, high byte (big-endian)
 *   Address 3: SERIAL LOW       -- unit number, low byte
 *
 * The unit is stored as a 16-bit big-endian value, but by definition it never
 * leaves the range 0-99, so the high byte is always 0x00. The field is kept
 * 16-bit anyway: the layout is shared with the Q-1 and must not drift.
 *
 * DISPLAY FORMAT
 *   A single compact number SSNN, with NO separator: series without leading
 *   zeros, unit always two digits zero-padded.
 *
 *       series 20, unit 52  ->  2052
 *       series 21, unit  0  ->  2100
 *
 *   sprintf(buf, "%u%02u", series, unit);
 *
 *   The number is a continuous counter: the board after 2099 is 2100, which is
 *   series 21 unit 00. Valid range 100-25599 (series 1-255, unit 00-99).
 *
 *   The old SERIES-NNNN form (e.g. "20-0055") is obsolete and must not appear
 *   in the firmware, in the serial output, in the log files or in the GUI.
 *
 * ANTI-OVERWRITE PROTECTION
 *   If the EEPROM already holds a valid serial number (magic byte present) the
 *   programmer will NOT overwrite it. The operator has to send 'Y' over the
 *   serial monitor to confirm.
 *
 * USAGE
 *   1. Set OPENQCM_SERIALNUMBER below to the SSNN of the board
 *   2. Flash this sketch to the Teensy
 *   3. Open the Serial Monitor at 115200 baud
 *   4. Verify the number it prints back
 *   5. Flash the operational firmware -- the EEPROM survives it
 *
 * author     Marco Mauro
 * version    1.0
 * date       August 2026
 */

#include <EEPROM.h>

/*************************** EEPROM LAYOUT ***************************/
#define ADDR_MAGIC        0
#define ADDR_SERIES       1
#define ADDR_SERIAL_HIGH  2
#define ADDR_SERIAL_LOW   3

#define MAGIC_BYTE  0xA5

/**************** CONFIGURE THIS BEFORE EACH BOARD *******************/
#define OPENQCM_SERIALNUMBER   1900   // SSNN: series * 100 + unit
/*********************************************************************/

/* One macro, two fields: the split is the format's own arithmetic and is done
   at compile time, so the sketch cannot be flashed with a series and a unit
   that disagree. */
#define OPENQCM_SERIES   (OPENQCM_SERIALNUMBER / 100)
#define OPENQCM_UNIT     (OPENQCM_SERIALNUMBER % 100)

#if (OPENQCM_SERIALNUMBER < 100) || (OPENQCM_SERIALNUMBER > 25599)
#error "OPENQCM_SERIALNUMBER out of range: valid SSNN is 100 to 25599 (series 1-255, unit 00-99)"
#endif

bool waitingConfirmation = false;
bool programmingDone = false;

/* Format a series/unit pair the one way the specification allows */
void formatSerial(char *buf, byte series, uint16_t unit) {
  sprintf(buf, "%u%02u", series, unit);
}

/* Write the configured serial number into EEPROM */
void writeSerialNumber() {
  EEPROM.write(ADDR_MAGIC, MAGIC_BYTE);
  EEPROM.write(ADDR_SERIES, (byte)OPENQCM_SERIES);
  EEPROM.write(ADDR_SERIAL_HIGH, (OPENQCM_UNIT >> 8) & 0xFF);
  EEPROM.write(ADDR_SERIAL_LOW, OPENQCM_UNIT & 0xFF);
}

/* Read the serial number stored in EEPROM. Returns false when the magic byte
   is missing, which means the board has never been programmed -- the caller
   must report that and must not invent a number. */
bool readSerialNumber(byte *series, uint16_t *unit) {
  if (EEPROM.read(ADDR_MAGIC) != MAGIC_BYTE) {
    return false;
  }
  *series = EEPROM.read(ADDR_SERIES);
  *unit = ((uint16_t)EEPROM.read(ADDR_SERIAL_HIGH) << 8)
        | EEPROM.read(ADDR_SERIAL_LOW);
  return true;
}

/* Print what the EEPROM holds right now */
void printStoredSerial() {
  byte series;
  uint16_t unit;
  if (!readSerialNumber(&series, &unit)) {
    Serial.println("  (no serial number programmed)");
    return;
  }
  char buf[16];
  formatSerial(buf, series, unit);
  Serial.print("  ");
  Serial.println(buf);
}

/* Print the value this sketch is configured to write */
void printNewSerial() {
  char buf[16];
  formatSerial(buf, (byte)OPENQCM_SERIES, (uint16_t)OPENQCM_UNIT);
  Serial.print("  ");
  Serial.println(buf);
}

void setup() {
  Serial.begin(115200);
  delay(2000);  // wait for the Serial Monitor to connect

  Serial.println("==========================================");
  Serial.println("  openQCM NEXT Serial Number Programmer");
  Serial.println("==========================================");
  Serial.println();

  if (EEPROM.read(ADDR_MAGIC) == MAGIC_BYTE) {
    // A serial number already exists -- anti-overwrite protection
    Serial.println("WARNING: this board already has a serial number!");
    Serial.println();
    Serial.println("Existing serial:");
    printStoredSerial();
    Serial.println();
    Serial.println("New serial to program:");
    printNewSerial();
    Serial.println();
    Serial.println("Send 'Y' to overwrite, any other key to abort.");
    waitingConfirmation = true;
  } else {
    // Virgin EEPROM -- program directly
    Serial.println("No existing serial number found. Programming...");
    Serial.println();
    writeSerialNumber();
    programmingDone = true;
    Serial.println("Done! Serial number programmed:");
    printStoredSerial();
    Serial.println();
    Serial.println("Verify the number above, then flash the operational firmware.");
  }
}

void loop() {
  // Handle the overwrite confirmation
  if (waitingConfirmation && Serial.available() > 0) {
    char c = Serial.read();
    // Drain what is left (the Serial Monitor sends \r\n)
    while (Serial.available() > 0) Serial.read();

    if (c == 'Y' || c == 'y') {
      Serial.println();
      Serial.println("Overwriting serial number...");
      Serial.println();
      writeSerialNumber();
      programmingDone = true;
      Serial.println("Done! New serial number programmed:");
      printStoredSerial();
      Serial.println();
      Serial.println("Verify the number above, then flash the operational firmware.");
    } else {
      Serial.println();
      Serial.println("Aborted. Existing serial number preserved:");
      printStoredSerial();
      programmingDone = true;
    }
    waitingConfirmation = false;
  }

  // Periodic verification line. This is the contract the host parses: a plain
  // integer, no dash, no leading zeros on the series.
  if (programmingDone) {
    delay(3000);
    byte series;
    uint16_t unit;
    if (readSerialNumber(&series, &unit)) {
      char buf[16];
      formatSerial(buf, series, unit);
      Serial.print("SERIALNUMBER = ");
      Serial.println(buf);
    } else {
      Serial.println("SERIALNUMBER = NONE");
    }
  }
}
