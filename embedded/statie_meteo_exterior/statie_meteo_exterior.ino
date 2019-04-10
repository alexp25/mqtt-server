/**
   Statie meteo exterior
*/
#include <SPI.h>
#include <SD.h>
#include <Wire.h>
#include <TimeLib.h>
#include <DS1307RTC.h>
#include "CustomSoftwareSerial.h"
CustomSoftwareSerial* customSerial;

#define MAX485_DE 4
#define MAX485_RE_NEG 5

#define STATION_ID 0xA1

#define RESP_MSG_LEN 20
#define REQ_MSG_LEN 7

uint8_t enable_time = 0, enable_file = 0;
#define DATA_LEN 5

uint8_t req_msg[REQ_MSG_LEN] = {STATION_ID, 0x6F, 0, 0, DATA_LEN, 0, 7};

long measurements[DATA_LEN];
long counter = 0;

uint8_t addr = STATION_ID;

uint8_t resp_msg[RESP_MSG_LEN];
short resp_msg_index = 0;
short send_flag = 0, recv_flag = 0;

uint16_t crc;
uint32_t t0;
uint32_t t0_recv;
uint32_t t0_recv_timeout;
uint32_t t1_recv;

char msg[50];

uint32_t t0_mqtt;
uint8_t led_state = 0;
File myFile;
char timestamp[25];


void write_to_card();

void init_data() {
  crc = CRC16(req_msg, REQ_MSG_LEN);
}

/* Calcul CRC pentru mesajul dat */
unsigned int CRC16 (unsigned char *puchMsg, unsigned short usDataLen )
{
  unsigned int crc = 0xFFFF ;    /* initializare registru CRC */
  while (usDataLen--)         /* se parcurge mesajul */
  {
    unsigned int aux;   /* se calculeaza suma CRC pentru un byte */
    aux = crc ^ *puchMsg++;
    aux = aux ^ (aux << 1);
    aux = aux ^ (aux << 2);
    aux = aux ^ (aux << 4);
    aux &= 0xFF;
    crc = (crc >> 8) ^ (aux << 6) ^ (aux << 8) ^ (aux >> 7);
  }
  return crc;
}

void check_rx(boolean wait = false) {
  if (customSerial->available()) {
    delay(200);
    while (customSerial->available()) {
      if (resp_msg_index < RESP_MSG_LEN) {
        resp_msg[resp_msg_index] = customSerial->read();
        resp_msg_index++;
      }
    }

    Serial.println((char*)resp_msg);
    parse_msg();

    uint32_t t1_recv = millis();

    if (enable_file) {
      if (t1_recv - t0_recv >= 10000) {
        t0_recv = t1_recv;
        write_to_card();
      }
    }

    if (t1_recv - t0_mqtt >= 2000) {
      t0_mqtt = t1_recv;
      Serial.println(msg);
    }


    recv_flag = 1;
  }
}

void print2digits(int number) {
  if (number >= 0 && number < 10) {
    sprintf(timestamp, "%s%d", timestamp, 0);
  }
  sprintf(timestamp, "%s%d", timestamp, number);
}

void read_time() {
  tmElements_t tm;
  memset(timestamp, 0, sizeof(timestamp));
  if (RTC.read(tm)) {
    sprintf(timestamp, "%d/", tm.Day);
    sprintf(timestamp, "%s%d/", timestamp, tm.Month);
    sprintf(timestamp, "%s%d,", timestamp, tmYearToCalendar(tm.Year));
    print2digits(tm.Hour);
    sprintf(timestamp, "%s:", timestamp);
    print2digits(tm.Minute);
    sprintf(timestamp, "%s:", timestamp);
    print2digits(tm.Second);
  } else {
    if (RTC.chipPresent()) {
      Serial.println("dbg, The DS1307 is stopped. Please run the SetTime");
    } else {
      Serial.println("dbg, DS1307 read error!  Please check the circuitry.");
    }
    delay(9000);
  }
}

void write_to_card() {
  myFile = SD.open("test.txt", FILE_WRITE);

  // if the file opened okay, write to it:
  if (myFile) {
    myFile.println(msg);
    Serial.println("dbg, write to SD");
    myFile.close();
  } else {
    // if the file didn't open, print an error:
    Serial.println("dbg, error opening file");
  }
}

void parse_msg() {
  char msgbuf[10];
  if (resp_msg[0] == STATION_ID && resp_msg[1] == 0x6F) {
    strcpy(msg, "data,");
    for (int i = 0; i < 5; i++) {
      measurements[i] = (long)resp_msg[2 + i * 2] * 256 + resp_msg[2 + i * 2 + 1];
      sprintf(msgbuf, "%ld,", measurements[i]);
      strcat(msg, msgbuf);
    }
    if (enable_time) {
      read_time();
      strcat(msg, timestamp);
    }
    resp_msg_index = 0;
  } else {
    resp_msg_index = 0;
  }
}


void check_cmd() {
  if (Serial.available()) {
    Serial.read();
    send_flag = 1;
  }
}

//DE (data enable) and RE (receive enable)
void preTransmission()
{
  digitalWrite(MAX485_RE_NEG, 0);
  digitalWrite(MAX485_DE, 1);
}

void postTransmission()
{
  digitalWrite(MAX485_RE_NEG, 0);
  digitalWrite(MAX485_DE, 1);
}

void setup()
{

  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
  pinMode(6, OUTPUT);
  digitalWrite(6, 1);
  pinMode(7, OUTPUT);
  digitalWrite(7, 1);

  pinMode(MAX485_RE_NEG, OUTPUT);
  pinMode(MAX485_DE, OUTPUT);
  postTransmission();
  init_data();
  Serial.begin(250000);
  customSerial = new CustomSoftwareSerial(8, 9); // rx, tx
  customSerial->begin(19200, CSERIAL_8E1);
  t0 = millis();
  t0_recv = t0;
  t0_recv_timeout = t0;
  t0_mqtt = t0;
  if (enable_file) {
    if (!SD.begin(2)) {
      Serial.println("dbg, sd initialization failed!");
      return;
    }
  }
}


void loop()
{
  uint8_t result;
  uint32_t t1 = millis();
  check_rx();
  //  check_cmd();

  if ((t1 - t0 >= 500) || send_flag) {
    send_flag = 0;
    digitalWrite(13, 1);
    t0 = t1;

    //    Serial.println("Send");
    preTransmission();
    delay(10);
    for (short i = 0; i < REQ_MSG_LEN; i++) {
      customSerial->write((uint8_t)req_msg[i]);
    }
    customSerial->write((uint8_t)crc);
    customSerial->write((uint8_t)(crc >> 8));
    //       Serial.println("Sent");
    //    customSerial->flush();
    delay(10);
    postTransmission();
  }


  if ((t1 - t0_recv_timeout >= 3000) || recv_flag) {
    digitalWrite(13, 0);
    if (!recv_flag) {
      delay(1000);
    }
    recv_flag = 0;
    t0_recv_timeout = t1;
  }
}

