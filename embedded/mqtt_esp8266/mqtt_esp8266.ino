#include <ESP8266WiFi.h>
#include <MQTTClient.h>

#include "mqtt_io.h"
//#include "def_test.h"
//#include "def_ws.h"
#include "def_ws.h"
//#include "def_gas_sensor.h"
// #include "def_blank_sensor.h"

#include "SerialParser.h"


WiFiClient WiFimqttClient;
MQTTClient mqttClient;

SerialParser s;


#define N_BUF_SERIAL 100
//serial/tcp data
char serialBufferIn[N_BUF_SERIAL];
uint8_t serialBuffer[N_BUF_SERIAL];
int serialBufferIndex = 0;
unsigned long lastMillis, crtMillis;


void connect_wifi() {
  Serial.println("255,0");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("255,1");
}


void setup() {
  //  Serial.begin(115200);
  Serial.begin(250000);
  delay(10);
  Serial.println();
  Serial.println();
  Serial.print("254, Connecting to ");
  Serial.println(ssid);



#ifdef WPA2
  // WPA2 enterprise magic starts here
  //  not working
  WiFi.disconnect(true);
  //  esp_wifi_sta_wpa2_ent_set_identity((uint8_t *)username, strlen(EAP_ID));
  esp_wifi_sta_wpa2_ent_set_username((uint8_t *)username, strlen(username));
  esp_wifi_sta_wpa2_ent_set_password((uint8_t *)password, strlen(password));
  esp_wifi_sta_wpa2_ent_enable();
  // WPA2 enterprise magic ends here
  WiFi.begin(ssid);
#endif

#ifndef WPA2
  WiFi.begin(ssid, password);
#endif

  connect_wifi();

  Serial.println("254, WiFi connected");
  Serial.print("254, IP address: ");
  Serial.println(WiFi.localIP());
  delay(2000);

  Serial.print("254, connecting to MQTT broker: ");
  Serial.print(broker);
  Serial.println();
  mqttClient.begin(broker, WiFimqttClient);
  mqttClient.onMessage(received_mqtt);
  mqtt_connect();

#ifdef WITH_SENSOR
  init_sensor();
#endif

  lastMillis  = millis();
}



void mqtt_connect() {
  Serial.println("255,0");
  //  mqttClient_id, mqtt broker username, mqtt broker password
  while (!mqttClient.connect(nodeId, mqttUser, mqttPassword)) {
    Serial.print(".");
  }
  Serial.println("\n254,connected!");
  mqttClient.subscribe(topicIn);
  Serial.println("255,1");
}


void onreceive(char* data){
 send_mqtt(topicOut, (String)((char*)data));  
}


void send_mqtt(String topic, String data) {
  //  mqttClient.publish("wsn/indoor_ws", (String)val);
  Serial.println("254, mqtt send: " + topic + ", data: " + data);
  mqttClient.publish(topic, data);
}


void received_mqtt(String &topic, String &payload) {
  // a user friendly message, ignored by the connected device
  Serial.println("254, mqtt receive: " + topic + " - " + payload);
  // the actual command that will be decoded by the connected device
  Serial.println(payload);
}

void loop() {
  //  int val = analogRead(A0);

  if (WiFi.status() != WL_CONNECTED) {
    connect_wifi();
  }

  mqttClient.loop();
  if (!mqttClient.connected()) {
    mqtt_connect();
  }

  s.check_com_raw(&onreceive);

#ifdef WITH_SENSOR
  crtMillis = millis();
  if (crtMillis - lastMillis > 2000) {
    lastMillis = crtMillis;
    read_sensor();
    formatOutput(send_array_data, 1, send_buf);
    if (withEndline) {
      strcat(send_buf, "\n");
    }
    send_mqtt(topicOut, send_buf);
  }
#endif

}
