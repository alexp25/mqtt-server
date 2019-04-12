/**
   Statie meteo exterior
*/
#include <Wire.h>
#include "CustomSoftwareSerial.h"
CustomSoftwareSerial* customSerial;

#define MAX485_DE 4
#define MAX485_RE_NEG 5

#define STATION_ID 0xA1

#define RESP_MSG_LEN 30
#define REQ_MSG_LEN 7

#define DATA_LEN 8

uint8_t req_msg[REQ_MSG_LEN] = {STATION_ID, 0x6F, 0, 0, DATA_LEN, 0, 7};

long measurements[DATA_LEN];
long measurements_counter[DATA_LEN];
long measurements_filtered[DATA_LEN];
int n_filter = 20;

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
char timestamp[25];

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

    //    Serial.println((char*)resp_msg);
    parse_msg();

    uint32_t t1_recv = millis();

    if (t1_recv - t0_mqtt >= 2000) {
      t0_mqtt = t1_recv;
      Serial.println(msg);
    }

    recv_flag = 1;
  }
}

void parse_msg() {
  char msgbuf[10];
  if (resp_msg[0] == STATION_ID && resp_msg[1] == 0x6F) {

    for (int i = 0; i < DATA_LEN; i++) {
      measurements[i] = (long)resp_msg[2 + i * 2] * 256 + resp_msg[2 + i * 2 + 1];
    }

    filter_measurements(measurements_filtered, measurements, measurements_counter, DATA_LEN, n_filter);

    strcpy(msg, "data,");
    for (int i = 0; i < DATA_LEN; i++) {
      sprintf(msgbuf, "%ld,", measurements_filtered[i]);
      strcat(msg, msgbuf);
    }

    resp_msg_index = 0;
  } else {
    resp_msg_index = 0;
  }
}

int init_filter = 1;
int index_filter = 0;

void filter_measurements(long* filtered, long* measurements, long* measurements_counter, int len, int n_filter) {
 
  if (init_filter == 1) {
    for (int i = 0; i < len; i++) {
      filtered[i] = measurements[i];
    }
  }

  if (index_filter >= n_filter) {
    index_filter = 0;
    init_filter = 0;
    for (int i = 0; i < len; i++) {
      filtered[i] = measurements_counter[i] / n_filter;
      measurements_counter[i] = 0;
    }
  }

  for (int i = 0; i < len; i++) {
    measurements_counter[i] += measurements[i];
  }
  index_filter += 1;
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

