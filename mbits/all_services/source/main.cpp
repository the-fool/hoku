// #include <unistd.h>
#include "MicroBit.h"
#include "MicroBitUARTService.h"
#include "ubit-neopixel/uBit_neopixel.h"

int x, r, b;
int contacted = 0;
char buffer[64];
int pitch, roll, roll_quad, pitch_quad, face;
int LED_LEN = 1;
int connected = 0;
int i = 0, j = 0;
MicroBit uBit;
_neopixel_strip_t pixels;
MicroBitI2C i2c = MicroBitI2C(I2C_SDA0, I2C_SCL0);
MicroBitAccelerometer acc = MicroBitAccelerometer(i2c);
MicroBitUARTService *uart;
MicroBitPin P0(MICROBIT_ID_IO_P0, MICROBIT_PIN_P0, PIN_CAPABILITY_ALL); 
MicroBitSerial serial(USBTX, USBRX); 

void onConnected(MicroBitEvent)
{
  uBit.display.print("C");
  connected = 1;
}

void onDisconnected(MicroBitEvent)
{
  uBit.display.print("D");
  connected = 0;
}

int getQuad(int deg) {
  if (deg > -45 && deg <= 45) {
    return 0;
  }

  if (deg >  45 && deg <= 90 + 45) {
    return 1;
  }
  if (deg > 90 + 45 || deg < -180 + 45) {
    return 2;
  }

  return 3;
}

int calcFace(int pitch_quad, int roll_quad) {
  if (pitch_quad == 0) {
    // front or back
    return roll_quad;
  }
  if (pitch_quad == 1) {
    return 4;
  }
  if (pitch_quad == 3) {
    return 5;
  }
  return 5;
}

int getFace()
{
  pitch = acc.getPitch();
  roll = acc.getRoll();

  roll_quad = getQuad(roll);
  pitch_quad = getQuad(pitch);

  return calcFace(pitch_quad, roll_quad);
}

void onContact(MicroBitEvent)
{
  x = P0.getDigitalValue();
  if (x == contacted) {
    return;
  }
  contacted = x;

  face = getFace();


  //sprintf(buffer, "p:%d r:%d pq:%d rq:%d\n", pitch, roll, pitch_quad, roll_quad);
  //uBit.display.scroll(face);
  //serial.send(buffer);

  sprintf(buffer, "%d%d", contacted, face);
  uart->send(buffer);
  uBit.sleep(500);
}

void onButtonA(MicroBitEvent)
{
  face = getFace();
  sprintf(buffer, "1%d", face);
  uart->send(buffer);
  uBit.sleep(500);
}

int main() {

  uBit.init();
  uBit.display.scroll("GO");

  uBit.serial.baud(115200);
  acc.setRange(1);
  acc.setPeriod(20);

  uBit.messageBus.listen(MICROBIT_ID_BLE, MICROBIT_BLE_EVT_CONNECTED, onConnected);
  uBit.messageBus.listen(MICROBIT_ID_BLE, MICROBIT_BLE_EVT_DISCONNECTED, onDisconnected);

  uBit.messageBus.listen(MICROBIT_ID_IO_P0, MICROBIT_BUTTON_EVT_UP, onContact);
  uBit.messageBus.listen(MICROBIT_ID_IO_P0, MICROBIT_BUTTON_EVT_DOWN, onContact);
  uBit.io.P0.isTouched();
  // new MicroBitAccelerometerService(*uBit.ble, uBit.accelerometer);
  uart = new MicroBitUARTService(*uBit.ble, 32, 32);
  neopixel_init(&pixels, MICROBIT_PIN_P0, LED_LEN);

  uBit.messageBus.listen(MICROBIT_ID_BUTTON_A, MICROBIT_BUTTON_EVT_CLICK, onButtonA);
  /*

  while (1) {
    j = (j + 1) % 8;

    x = acc.getRoll();

    if (connected && j == 0) {
      uart->send(x);
    }

    x = x > 0 ? x : x * -1;

    b = (int)floor(0 + (x * 255/180));
    r = (int)floor(255 - (x * 255/180));

    for (i = 0; i < LED_LEN; i++)
      neopixel_set_color_and_show(&pixels, i, r, 20, b);

    uBit.sleep(20);
  }
  */

  while(1)
    uBit.sleep(50);

  release_fiber();
}
