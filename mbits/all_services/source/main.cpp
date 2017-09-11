// #include <unistd.h>
#include "MicroBit.h"
#include <math.h>
#include "ubit-neopixel/uBit_neopixel.h"

_neopixel_strip_t pixels;
MicroBitI2C i2c = MicroBitI2C(I2C_SDA0, I2C_SCL0);
MicroBitAccelerometer accelerometer = MicroBitAccelerometer(i2c);
int x, r, b, i;
double roll_radians, x1;
MicroBit uBit;
char str[32];
int main() {
  uBit.init();
  uBit.display.scroll("GO");

  accelerometer.setRange(1);
  accelerometer.setPeriod(20);

  neopixel_init(&pixels, MICROBIT_PIN_P0, 1);

  while (1) {
    x = accelerometer.getRoll();
    x1 = x > 0 ? x : x * -1;
    //uBit.display.print(x);
    b = (int)floor(0 + (x1 * 255/180));
    r = (int)floor(255 - (x1 * 255/180));
    neopixel_set_color_and_show(&pixels, 0, r, 20, b);
    //neopixel_show(&pixels);
    uBit.sleep(20);
  }
  release_fiber();
}
