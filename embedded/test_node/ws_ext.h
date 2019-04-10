

#ifndef __WS_EXT__
#define __WS_EXT__

#include <stdint.h>
#include <Arduino.h>
#include "CustomSoftwareSerial.h"

#ifdef __cplusplus
extern "C"
{
#endif

#ifndef MAX485_DE
#define MAX485_DE 4
#endif
#ifndef MAX485_RE_NEG
#define MAX485_RE_NEG 5
#endif

// exterior
#define STATION_ID 0xA1
#define REQ_MSG_LEN 7
#define DATA_LEN 8


CustomSoftwareSerial* customSerial;

    char msgnames[DATA_LEN][15] = {"temp: \0", "hum: \0", "w speed: \0", "w dir: \0", "rs: \0", "st: \0", "red: \0", "blue: \0"};
    uint8_t req_msg[REQ_MSG_LEN] = {STATION_ID, 0x6F, 0, 0, DATA_LEN, 0, 7};
    long measurements[DATA_LEN];
    uint8_t addr = STATION_ID;
    uint8_t resp_msg[RESP_MSG_LEN];
    short resp_msg_index = 0;
    short send_flag = 0;
    uint16_t crc;
    uint32_t t0;

    void _ws_init_data()
    {
        crc = CRC16(req_msg, REQ_MSG_LEN);
    }

    unsigned int _ws_CRC16(unsigned char *puchMsg, unsigned short usDataLen) /* Functia returneaza suma CRC pentru mesajul dat */
    {
        unsigned int crc = 0xFFFF; /* initializare registru CRC */
        while (usDataLen--)        /* se parcurge mesajul */
        {
            unsigned int aux; /* se calculeaza suma CRC pentru un byte */
            aux = crc ^ *puchMsg++;
            aux = aux ^ (aux << 1);
            aux = aux ^ (aux << 2);
            aux = aux ^ (aux << 4);
            aux &= 0xFF;
            crc = (crc >> 8) ^ (aux << 6) ^ (aux << 8) ^ (aux >> 7);
        }
        return crc;
    }

    void _ws_check_rx(boolean wait = false)
    {
        if (customSerial->available())
        {
            while (customSerial->available())
            {
                resp_msg[resp_msg_index] = customSerial->read();
                resp_msg_index++;
            }
            _ws_parse_msg();
        }
    }

    void _ws_parse_msg()
    {
        char msg[100];
        char msgbuf[10];

        if (resp_msg[0] == STATION_ID && resp_msg[1] == 0x6F)
        {
            //    Serial.print("recv: ");
            //    for (short i = 0; i < resp_msg_index; i++) {
            //      Serial.print(resp_msg[i], HEX);
            //      Serial.print(" ");
            //    }

            strcpy(msg, "");

            sprintf(msgbuf, "%ld. ", counter);
            strcat(msg, msgbuf);
            counter++;

            for (int i = 0; i < DATA_LEN; i++)
            {
                measurements[i] = (long)resp_msg[2 + i * 2] * 256 + resp_msg[2 + i * 2 + 1];
                strcat(msg, msgnames[i]);
                sprintf(msgbuf, "%ld, ", measurements[i]);
                strcat(msg, msgbuf);
            }

            strcat(msg, "\n");


            Serial.print(msg);


            resp_msg_index = 0;
        }
        else
        {
            resp_msg_index = 0;
        }
    }

    //DE (data enable) and RE (receive enable)
    void _ws_pre_transmission()
    {
        //  digitalWrite(MAX485_RE_NEG, 1);
        //  digitalWrite(MAX485_DE, 1);
        digitalWrite(MAX485_RE_NEG, 0);
        digitalWrite(MAX485_DE, 1);
    }

    void _ws_post_transmission()
    {
        //  digitalWrite(MAX485_RE_NEG, 0);
        //  digitalWrite(MAX485_DE, 0);
        digitalWrite(MAX485_RE_NEG, 0);
        digitalWrite(MAX485_DE, 1);
    }

    void _ws_transmit()
    {
        _ws_pre_transmission();
        delay(10);
        for (short i = 0; i < REQ_MSG_LEN; i++)
        {
            customSerial->write((uint8_t)req_msg[i]);
        }
        customSerial->write((uint8_t)crc);
        customSerial->write((uint8_t)(crc >> 8));
        //customSerial->flush();
        delay(10);
        _ws_post_transmission();
    }

    void _ws_setup()
    {
        pinMode(MAX485_RE_NEG, OUTPUT);
        pinMode(MAX485_DE, OUTPUT);
        _ws_post_transmission();
        _ws_init_data();
        customSerial = new CustomSoftwareSerial(8, 9); // rx, tx
        customSerial->begin(19200, CSERIAL_8E1);
        t0 = millis();
    }

#ifdef __cplusplus
}
#endif

#endif