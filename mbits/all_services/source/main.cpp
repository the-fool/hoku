// #include <unistd.h>
#include "MicroBit.h"
#include "MicroBitUARTService.h"
#include "ubit-neopixel/uBit_neopixel.h"

MicroBit uBit;
_neopixel_strip_t pixels;
MicroBitI2C i2c = MicroBitI2C(I2C_SDA0, I2C_SCL0);
MicroBitAccelerometer acc = MicroBitAccelerometer(i2c);
MicroBitUARTService *uart;
MicroBitPin P0(MICROBIT_ID_IO_P0, MICROBIT_PIN_P0, PIN_CAPABILITY_DIGITAL);
MicroBitSerial serial(USBTX, USBRX);

int i, r, g, b;
char buffer[64];

int pitch, roll, roll_quad, pitch_quad;

int* color;

#define RED {209,0,0}
#define ORANGE {255,102,34}
#define YELLOW {255,218,33}
#define GREEN {51,221,0}
#define BLUE {17,51,204}
#define VIOLET {200,10,200}
#define WHITE {250, 250, 250}

int COLORS[6][3] = { RED, YELLOW, GREEN, BLUE, VIOLET, WHITE };
int ble_connected = 0;
int contacted;
int LED_LEN = 1;
int prev_face = -1;
int face;

void setColor(int face) {
  color = COLORS[face];

  for (i = 0; i < LED_LEN; i++)
    neopixel_set_color_and_show(&pixels, i, color[0], color[1], color[2]);
}

void onConnected(MicroBitEvent) {
  uBit.display.print("C");
  ble_connected = 1;
}

void onDisconnected(MicroBitEvent) {
  uBit.display.print("D");
  ble_connected = 0;
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
  // 0 - 5
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

void getFace()
{
  pitch = acc.getPitch();
  roll = acc.getRoll();

  roll_quad = getQuad(roll);
  pitch_quad = getQuad(pitch);

  face = calcFace(pitch_quad, roll_quad);
}

void doIt() {
  getFace();

  if (face != prev_face) {
    prev_face = face;

    uBit.display.scrollAsync(face);

    setColor(face);

    sprintf(buffer, "1%d", face);
    uart->send(buffer);
    uBit.sleep(500);
  }
}

void poll() {
  contacted = P0.getDigitalValue();

  if (contacted) {
    doIt();
  }
}


void onButtonA(MicroBitEvent)
{
  uBit.display.scrollAsync('A');
  getFace();

  setColor(face);

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

  uart = new MicroBitUARTService(*uBit.ble, 32, 32);
  neopixel_init(&pixels, MICROBIT_PIN_P2, LED_LEN);

  uBit.messageBus.listen(MICROBIT_ID_BUTTON_A, MICROBIT_BUTTON_EVT_CLICK, onButtonA);

  while (1) {
    uBit.sleep(100);
    poll();
  }

  release_fiber();
}
