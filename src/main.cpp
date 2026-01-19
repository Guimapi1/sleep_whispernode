#include <Arduino.h>
#include <LowPower.h>
#include <LoRa.h>
#include <T2WhisperNode.h>


T2Flash myFlash;

void setup() {
    myFlash.init(T2_WPN_FLASH_SPI_CS);
    LoRa.setPins(10,7,2);
    if (!LoRa.begin(868E6)) {
        while (1);
  }
}

void loop() {
  delay(1000);
  analogWrite(A1, 0);
  myFlash.powerDown();
  LoRa.sleep();
  LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);
}