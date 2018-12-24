#include <ESP8266WiFi.h>
#include <MQTTClient.h>


const char* ssid     = "TP-LINK_70E4";
const char* password = "27120132";

WiFiClient WiFiclient;
MQTTClient client;

unsigned long lastMillis = 0;

void setup() {
  Serial.begin(115200);
  delay(10);
  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  delay(2000);

  Serial.print("connecting to MQTT broker...");
  //  client.begin("broker.shiftr.io", WiFiclient);
  client.begin("192.168.12.160", WiFiclient);
  client.onMessage(messageReceived);
  connect();
}

void messageReceived(String &topic, String &payload) {
  Serial.println("incoming: " + topic + " - " + payload);
}

void connect() {
  //  client_id, mqtt broker username, mqtt broker password
  while (!client.connect("indoor_ws", "username", "password")) {
    Serial.print(".");
  }
  Serial.println("\nconnected!");
  //  client.subscribe("wsn/#");
  client.subscribe("wsn/check");
}

int val = 0;

void loop() {
  //  int val = analogRead(A0);
  client.loop();
  if (!client.connected()) {
    connect();
  }

  if (millis() - lastMillis > 1000) {
    lastMillis = millis();

    val += 1;
    if (val > 1000) {
      val = 0;
    }
    client.publish("wsn/indoor_ws", (String)val);
  }
}
