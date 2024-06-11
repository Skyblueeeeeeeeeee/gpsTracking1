#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <SoftwareSerial.h>
#include <TinyGPS++.h>
#include <DHT.h>
#include <ArduinoJson.h>
int btn1;
int btn2;
int btn3;
int btn4;
#define WIFI_AP "gps"
#define WIFI_PASSWORD "12345678"
#define TOKEN "2ZKFUdbBf2xAuPDPXG4l"
char thingsboardServer[] = "thingsboard.cloud";
const int thingsboardPort = 1883;
WiFiClient espClient;
PubSubClient client(espClient);
const char* host = "1.55.90.20"; // Địa chỉ IP của server
int khoa;
bool sbtn;
bool door;
bool lock;
float latitude;
float longitude;
float speed;

const int DHTPIN = D7;
const int DHTTYPE = DHT11;
DHT dht(DHTPIN, DHTTYPE);
int status = WL_IDLE_STATUS;
unsigned long lastSend;
unsigned long lastReset; 
const unsigned long resetInterval = 600000;  
#define gpsRxPin 1 
#define gpsTxPin 3
SoftwareSerial neo6m(gpsTxPin, gpsRxPin);
TinyGPSPlus gps;
String cua1;
String cua2;
String cua3;
String cua4;
bool cua_1 = true;
bool cua_2 = true;
bool cua_3 = true;
bool cua_4 = true;
float previousLatitude = 0.0;
float previousLongitude = 0.0;
unsigned long previousMillis = 0;

void smartdelay_gps(unsigned long ms);
void resetIfTime();
float calculateSpeed(float lat1, float long1, float lat2, float long2);

void setup() {
  Serial.begin(9600);
  WiFi_conection();
  client.setServer(thingsboardServer, thingsboardPort);
  neo6m.begin(9600);
  dht.begin();
  lastReset = millis();
  pinMode(D1, INPUT_PULLUP);
  pinMode(D2, INPUT_PULLUP);
  pinMode(D3, INPUT_PULLUP);
  pinMode(D4, INPUT_PULLUP); 
  pinMode(D5, OUTPUT);
  pinMode(D6, OUTPUT);
  pinMode(D8, OUTPUT);
  digitalWrite(D1, HIGH);
  digitalWrite(D2, HIGH);
  digitalWrite(D3, HIGH);
  digitalWrite(D4, HIGH);
  digitalWrite(D8, LOW);
}

void loop() {
  resetIfTime();
  if (!client.connected()) {
    reconnect();
  }
  if (millis() - lastSend > 100)
   {
    doc_vi_tri();
    lastSend = millis();
  }

  client.loop();

}

void WiFi_conection() {
  Serial.println("Connecting to AP ...");
  WiFi.begin(WIFI_AP, WIFI_PASSWORD);
  if (WiFi.status() != WL_CONNECTED) {
    delay(100);
    Serial.print(".");
  }
  Serial.println("Connected to AP");
}

void reconnect() {
  if (!client.connected()) {
    status = WiFi.status();
    if (status != WL_CONNECTED) {
      WiFi_conection();
    }
    Serial.print("Connecting to ThingsBoard node ...");
    if (client.connect("ESP8266 Device", TOKEN, NULL)) {
      Serial.println("[DONE]");
    } else {
      Serial.print("[FAILED]");
      Serial.println(" : retrying in 5 seconds]");
      delay(5000);
    }
  }
}

void doc_vi_tri() {
  smartdelay_gps(1000);
  doc_trang_thai_cua();
  float h, t, speed;
  dht11(h, t);
  if (gps.location.isValid()) {
     latitude = gps.location.lat();
     longitude = gps.location.lng();
    speed = calculateSpeed(latitude, longitude, previousLatitude, previousLongitude);
    previousLatitude = latitude;
    previousLongitude = longitude;
    String topic = "v1/devices/me/telemetry";
    String mapsLink = "https://www.google.com/maps/place/" + String(latitude, 12) + "," + String(longitude, 12);
    String status = "GPS có kết nối";
    // Gửi phần 1: Thông tin về trạng thái của các cửa
    String payload1 = "{\"status\":\"" + status + "\",\"cua1\":\"" + cua1 + "\",\"cua2\":\"" + cua2 + "\",\"cua3\":\"" + cua3 + "\",\"cua4\":\"" + cua4 + "\",\"status\":\"" + status + "\"}";
    client.publish(topic.c_str(), payload1.c_str());
    // Gửi phần 2: Thông tin về vị trí và tốc độ
    String payload2 = "{\"longitude\":" + String(longitude, 12) + ",\"latitude\":" + String(latitude, 12) + ",\"speed_kmh\":" + String(speed, 1) + ",\"t\":\"" + String(t) + "\",\"h\":\"" + String(h) + "\"}";
    client.publish(topic.c_str(), payload2.c_str());
    Serial.print("Sending payload: ");
    Serial.println(payload1);
    Serial.println(payload2);
  } else {
    String topic = "v1/devices/me/telemetry";
    Serial.println("GPS không kết nối");
    String status = "GPS không kết nối";
    // Gửi phần 1: Thông tin về trạng thái của các cửa
    String payload1 = "{\"status\":\"" + status + "\",\"cua1\":\"" + cua1 + "\",\"cua2\":\"" + cua2 + "\",\"cua3\":\"" + cua3 + "\",\"cua4\":\"" + cua4 + "\",\"status\":\"" + status + "\"}";
    client.publish(topic.c_str(), payload1.c_str());
    // Gửi phần 2: Thông tin về vị trí và tốc độ
    String payload2 = "{\"longitude\":0.0,\"latitude\":0.0,\"speed_kmh\":0.0,\"t\":" + String(t) + ",\"h\":" + String(h) + "}";
    client.publish(topic.c_str(), payload2.c_str());
    Serial.print("Sending payload: ");
    Serial.println(payload1);
    Serial.println(payload2);
  }
}

void dht11(float &h, float &t){
  h = dht.readHumidity();
  t = dht.readTemperature();
  t -= 3;
  if (isnan(h) || isnan(t)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
}
void smartdelay_gps(unsigned long ms) // chương trình con đếm thời gian 
{
  unsigned long start = millis();
  do
  {
    while (neo6m.available())
      gps.encode(neo6m.read());
  } while (millis() - start < ms);
}
void resetIfTime() {
  // Check if it's time to reset the ESP8266
  if (millis() - lastReset >= resetInterval) {
    ESP.restart();
  }
}

float calculateSpeed(float lat1, float long1, float lat2, float long2) {
  float distance = TinyGPSPlus::distanceBetween(lat1, long1, lat2, long2);
  unsigned long currentMillis = millis();
  float timeInSeconds = (currentMillis - previousMillis) / 1000.0;
    if (timeInSeconds == 0) {
    return 0; // hoặc giá trị mặc định khác
  }
  previousMillis = currentMillis;
  speed = distance / timeInSeconds; // in meters per second
  speed *= 3.6; // convert to km/h
  if (speed <= 2) {
    speed = 0;
  } else if (speed > 2 && speed <= 10) {
    speed -= 2;
  } 
  return speed;
}


void receive(){
   WiFiClient client;
  const int httpPort = 3004;
  if (!client.connect(host, httpPort)) {
    Serial.println("Connection failed");
    return;
  }

  // Gửi yêu cầu HTTP tới server với tham số truy vấn
  client.print(String("GET /?source=esp8266 HTTP/1.1\r\n") +
               "Host: " + host + "\r\n" + 
               "Connection: close\r\n\r\n");
  delay(100);  // Tăng thời gian chờ để nhận phản hồi đầy đủ

  // Đọc phản hồi từ server
  String payload;
  bool headersEnded = false;
  while(client.available()){
    String line = client.readStringUntil('\n');
    if (line == "\r") {
      headersEnded = true; // Đánh dấu kết thúc phần tiêu đề
    }
    if (headersEnded) {
      payload += line; // Chỉ thêm nội dung sau phần tiêu đề
    }
  }
  
  // In toàn bộ phản hồi để kiểm tra
  Serial.println("Response:");
  Serial.println(payload);
  
  // Parse JSON response
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, payload);
  
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }

  // Gán giá trị vào biến khoa
  sbtn = doc["sbtn"];
  khoa = doc["khoa"];
  Serial.print("khoa: ");
  Serial.println(khoa);
  Serial.print("Trang thai nut bam: ");
  Serial.println(sbtn);
  client.stop();
  delay(100); 
}
void doc_trang_thai_cua() {
    receive();
  btn1 = digitalRead(D1)?1:0;
  btn2 = digitalRead(D2)?1:0;
  btn3 = digitalRead(D3)?1:0;
  btn4 = digitalRead(D4)?1:0;
  Serial.println(btn1);
  Serial.println(btn2);
  Serial.println(btn3);
  Serial.println(btn4);
  
  static unsigned long startTime = 0;
  static bool isD5High = false;

  if (((speed > 20 && door && lock) || khoa == 1) && !isD5High) {
    digitalWrite(D5, HIGH);
    startTime = millis();
    isD5High = true;
    door = false; // Đóng cửa khi tốc độ lớn hơn 20 hoặc khoa được kích hoạt
  }


  if (speed <= 10) {
    door = true; 
  }

  if (isD5High && millis() - startTime >= 1500) {
    digitalWrite(D5, LOW);
    isD5High = false;
  }
if(sbtn==1){
  digitalWrite(D6, HIGH);
}
else{
  digitalWrite(D6, LOW);
}
  if (!btn1) {
    cua1="0";
  } else {
    cua1="1";
  }
  if (!btn2) {
    cua2="0";
  } else {
     cua2="1";
  }

  if (!btn3) {
    cua3="0";
  } else {
     cua3="1";
  }
  if (!btn4) {
    cua4="0";
  } else {
     cua4="1";
  }
  if(cua1 == "1" && cua2 =="1" && cua3 =="1" && cua4 =="1"){
    lock=true;
  }
  else{
    lock =false;
  }
  }

