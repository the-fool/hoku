// #include <unistd.h>
#include "MicroBit.h"
#include "MicroBitUARTService.h"
#include "ubit-neopixel/uBit_neopixel.h"

int x, r, b;
int LED_LEN = 1;
int connected = 0;
int i = 0, j = 0;
MicroBit uBit;
_neopixel_strip_t pixels;
MicroBitI2C i2c = MicroBitI2C(I2C_SDA0, I2C_SCL0);
MicroBitAccelerometer accelerometer = MicroBitAccelerometer(i2c);
MicroBitUARTService *uart;

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

int main() {

  uBit.init();
  uBit.display.scroll("GO");

  accelerometer.setRange(1);
  accelerometer.setPeriod(20);

  uBit.messageBus.listen(MICROBIT_ID_BLE, MICROBIT_BLE_EVT_CONNECTED, onConnected);
  uBit.messageBus.listen(MICROBIT_ID_BLE, MICROBIT_BLE_EVT_DISCONNECTED, onDisconnected);

  // new MicroBitAccelerometerService(*uBit.ble, uBit.accelerometer);
  uart = new MicroBitUARTService(*uBit.ble, 32, 32);
  neopixel_init(&pixels, MICROBIT_PIN_P0, LED_LEN);

  while (1) {
    j = (j + 1) % 8;

    x = accelerometer.getRoll();

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

  release_fiber();
}
