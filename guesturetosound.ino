#include <EEPROM.h>

int flexPin[4] = {A0,A1,A2,A3};

int straightVal[4];
int bendVal[4];
int flexValue[4];

int buttonPin = 3;
int redLED = 8;
int blueLED = 9;

bool calibrationMode = false;

void setup()
{
  Serial.begin(9600);

  pinMode(buttonPin,INPUT_PULLUP);
  pinMode(redLED,OUTPUT);
  pinMode(blueLED,OUTPUT);

  loadCalibration();
}

void loop()
{
  if(digitalRead(buttonPin)==LOW)
  {
    delay(300);
    calibrate();
  }

  normalMode();
}

void calibrate()
{
  calibrationMode=true;

  digitalWrite(redLED,HIGH);
  Serial.println("Keep fingers STRAIGHT");

  delay(5000);

  for(int i=0;i<4;i++)
  {
    straightVal[i]=analogRead(flexPin[i]);
  }

  digitalWrite(redLED,LOW);

  digitalWrite(blueLED,HIGH);
  Serial.println("BEND fingers");

  delay(5000);

  for(int i=0;i<4;i++)
  {
    bendVal[i]=analogRead(flexPin[i]);
  }

  digitalWrite(blueLED,LOW);

  saveCalibration();

  calibrationMode=false;

  Serial.println("Calibration Finished");
}

void normalMode()
{
  for(int i=0;i<4;i++)
  {
    flexValue[i]=analogRead(flexPin[i]);

    int mappedVal = map(flexValue[i],straightVal[i],bendVal[i],0,100);

    Serial.print(mappedVal);
    Serial.print(" ");
  }

  Serial.println();

  delay(200);
}

void saveCalibration()
{
  int addr=0;

  for(int i=0;i<4;i++)
  {
    EEPROM.put(addr,straightVal[i]);
    addr+=2;
  }

  for(int i=0;i<4;i++)
  {
    EEPROM.put(addr,bendVal[i]);
    addr+=2;
  }
}

void loadCalibration()
{
  int addr=0;

  for(int i=0;i<4;i++)
  {
    EEPROM.get(addr,straightVal[i]);
    addr+=2;
  }

  for(int i=0;i<4;i++)
  {
    EEPROM.get(addr,bendVal[i]);
    addr+=2;
  }
}
