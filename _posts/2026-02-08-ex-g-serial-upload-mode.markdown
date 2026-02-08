---
layout: post
title:  "EX-G Serial Upload Mode"
date:   2026-02-08 12:30:03 -0800
categories: mice electronics arduino
---

Developing software for the 
[ESP32S3](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/) as a USB
input device has a friction point when making software updates. The ESP32S3
doesn't support serial upload while the USB serial bus is being used as a
HID (Human Interface Device). In order to get the ESP32S3 to use the serial bus
for uploading software, the boot button on the ESP32S3 board needs to be held
down while plugging it in. 

The button is fairly small and can be hard to hold down while plugging a cable
into the board. The long term plan is to have the ESP32S3 board inside of an
[EX-G][ex-g] for the project
[Converting a Wireless Trackball to Wired]({% post_url 2025-12-14-wired-trackball %}).
It won't be practical to 
[disassemble]({% post_url 2025-12-26-disassemble-ex-g %}) the EX-G anytime I
want to try out new software. It feels like an unnecessary constraint to find a
way to position the ESP32S3 board so that the boot button is accessible from
outside the case.

Many devices enter boot mode by holding down a button combination during power
on. I figured I could copy this idea. The plan is to get the ESP32S3 to enter a
"serial upload" mode when both the left and right click buttons of the EX-G are
held down during power on. Using two buttons helps prevent someone
unintentionally holding the left click down while plugging the device in.

The ESP32S3 code is written in Arduino. The implementation will look for the two
buttons being active during the `setup()` method of the Arduino sketch. If the
buttons stay active for 1 second, then a flag will be set to indicate the
"serial upload" mode. When this happens `setup()` will return early, this
prevents the `Mouse` library code from setting up the USB for HID.

The `loop()` function of the sketch will have a guard clause at the start that
checks the flag indicating "serial upload". When the flag is set, the `loop()`
will return early, preventing access to the uninitialized `Mouse` elements.

Below is the code that checks for the button presses. When the buttons are
pressed they will be `LOW`.

```c
bool serialUploadMode = false;

bool checkSerialUploadMode() {
  pinMode(mouseButtons[LEFT].pin, INPUT_PULLUP);
  pinMode(mouseButtons[RIGHT].pin, INPUT_PULLUP);
  unsigned long start = millis();
  while (millis() - start < 1000) {
    if (digitalRead(mouseButtons[LEFT].pin) != LOW ||
        digitalRead(mouseButtons[RIGHT].pin) != LOW) {
      return false;
    }
  }
  return true;
}

void setup() {
  serialUploadMode = checkSerialUploadMode();
  if (serialUploadMode) {
    return;
  }
  // ... Normal logic
}
void loop() {
  if (serialUploadMode) {
    return;
  }
  // ... Normal logic
}
```

The full code can be seen at
[ex-g.ino](https://github.com/speedyleion/ex-g/blob/d0b9ff8381c5f097e0b1c90f76f6a2a7d3858f97/ex-g.ino).

To test this logic out I compiled and uploaded the code. Then I plugged the
ESP32S3 in with no buttons pressed (no pins grounded). Running the command
`arduino-cli board list` from the terminal listed no USB connected devices. I
then unplugged, grounded pins `D2` and `D3` (the left and right click pines),
then plugged the ESP32S3 back in. After waiting for a second, re-running
`arduino-cli board list` showed the ESP32S3 available as a USB connected device.

This went pretty smoothly. I should have looked into this sooner as I was
fighting holding down the boot button correctly numerous times to upload new
software to the ESP32S3.

[ex-g]: https://elecomusa.com/products/ex-g-trackball-wireless-usb-copy
