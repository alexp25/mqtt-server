
#include <Wire.h>
#include <avr/io.h>
#include <inttypes.h>
#include <EEPROM.h>
#include "ws_ext.h"
#include "timers.h"

// https://arduino-test.esp8266.com/Arduino/versions/2.0.0/doc/installing.html
// #include "hardware/esp8266com/esp8266/libraries/ESP8266WiFi/src/ESP8266WiFi.h"
// #include <MQTTClient.h>

#include <ArduinoWiFi.h>
#include <MQTTClient.h>


int node_id = 10;
int node_type = 11;

//flags
short wifi_connected = 0, dblog = 0;
short pgm_mode = 0;
unsigned long t_start_pgm = 0;

//serial data
#define N_SERIAL_DATA_STR 50
#define N_SERIAL_DATA_VAL 10

// char inData[N_SERIAL_DATA_STR];
// char inData2[N_SERIAL_DATA_STR];
// int dataArray[N_SERIAL_DATA_VAL];
char serialSendBuffer[N_SERIAL_DATA_STR];

const char *ssid = "TP-LINK_70E4";
const char *password = "27120132";
WiFiClient WiFiclient;
MQTTClient client;

//data

void connect_wifi()
{
  delay(10);
  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  delay(2000);

  Serial.print("connecting to MQTT broker...");
  client.begin("broker.shiftr.io", WiFiclient);
  // client.begin("192.168.12.160", WiFiclient);
  client.onMessage(messageReceived);
  connect();
}

void messageReceived(String &topic, String &payload)
{
  Serial.println("incoming: " + topic + " - " + payload);
}

void connect_mqtt()
{
  //  client_id, mqtt broker username, mqtt broker password
  while (!client.connect("indoor_ws", "username", "password"))
  {
    Serial.print(".");
  }
  Serial.println("\nconnected!");
  //  client.subscribe("wsn/#");
  client.subscribe("wsn/check");
}

#define MEM_START_VALUE 10

void read_settings()
{
  int i = 0;
  char mem0 = EEPROM.read(i);
  i++;
  if (mem0 == MEM_START_VALUE)
  {
    node_id = EEPROM.read(i) * 256;
    i++;
    node_id += EEPROM.read(i);
  }
}

void write_settings()
{
  int i = 0;
  EEPROM.write(i, MEM_START_VALUE);
  i++;
  EEPROM.write(i, node_id >> 8);
  i++;
  EEPROM.write(i, node_id);
}

volatile uint8_t flag = 0;

ISR(TIMER1_COMPA_vect)
{
  flag = 1;
}

void setup()
{
  Serial.begin(38400);
  _ws_setup();
  timer1_init(1, 1024, 15625);
}

void print_data()
{
  sprintf(serialSendBuffer, "%d,%d,%d,%d\n", 1, node_id, node_type, pump_pwm);
  Serial.print(serialSendBuffer);
}

void loop()
{
  client.loop();
  if (!client.connected())
  {
    connect();
  }
  _ws_check_rx();
  if (flag)
  {
    flag = 0;
    // _ws_transmit();
    print_data();
    val += 1;
    if (val > 1000) {
      val = 0;
    }
    client.publish("wsn/indoor_ws", (String)val);
  }
}
