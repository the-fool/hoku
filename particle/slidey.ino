
TCPClient client;

byte server[] = { 172, 16, 103, 125 };

int counter = 0;
void setup() {


  // We are going to tell our device that D0 and D7 (which we named led1 and led2 respectively) are going to be output
  // (That means that we will be sending voltage to them, rather than monitoring voltage that comes from them)

  // It's important you do this here, inside the setup() function rather than outside it or in the loop function.
Serial.begin(9600);

  pinMode(A0, INPUT);
 while(!Serial.available()) Particle.process();

  Serial.println("connecting...");

  if (client.connect(server, 8888)) {
      Serial.println("connected");
  }
}

// Next we have the loop function, the other essential part of a microcontroller program.
// This routine gets repeated over and over, as quickly as possible and as many times as possible, after the setup function is called.
// Note: Code that blocks for too long (like more than 5 seconds), can make weird things happen (like dropping the network connection).  The built-in delay function shown below safely interleaves required background activity, so arbitrarily long delays can safely be done if you need them.

void loop() {
  // To blink the LED, first we'll turn it on...

  	Serial.printlnf("testing %d", ++counter);
  	Serial.printlnf("%d", analogRead(A0));
	delay(1000);

	 if (client.available()) {
	     client.write(16);
	 } else {
	     Serial.println("client unconnected");
	     if (client.connect(server, 8888)) {
	      Serial.println("connected");
	     } else {
	         Serial.println("could not connect");
	     }
	 }

  // And repeat!
}
