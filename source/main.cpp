#include "MicroBit.h"
MicroBit uBit;
int main() {
 uBit.init();
 uBit.display.scroll("NEW PROGRAM");
 release_fiber();
}
