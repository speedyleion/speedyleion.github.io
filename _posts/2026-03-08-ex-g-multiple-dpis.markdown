---
layout: post
title:  "EX-G adding two DPI modes"
date:   2026-03-08 14:00:03 -0700
categories: mice electronics arduino
---

My last [post]({% post_url 2026-02-15-ex-g-power-up-reset %}) on programming the
[EX-G](https://elecomusa.com/products/ex-g-trackball-wireless-usb-copy)
trackball was 3 weeks ago. In the post I tried to detect when the ball was
removed from the socket so I could force a power up reset of the 
[PMW3320DB-TYDU](https://www.epsglobal.com/Media-Library/EPSGlobal/Products/files/pixart/PMW3320DB-TYDU.pdf)
optical sensor. The reason for trying to do a power up reset was to try and
remedy situations where the PMW3320DB-TYDU sensor didn't work for fine precision
movements. The thinking being that the PMW3320DB-TYDU wasn't full powered before
it got the reset instructions.

The lack of fine precision movement scenario hasn't shown up in the last three
weeks of use. The EX-G trackball is used daily. It only does a fresh power up in
the mornings when I turn the computer on. While the issue hasn't reared its
head, it still lingers in the back of my mind. I don't like the idea of having
to unplug and re-plug the trackball to get it to behave.

My next idea to be able to send the power up reset commands to the
PMW3320DB-TYDU is to send the commands out when the low/high DPI switch changes
positions. The original EX-G controller only sent out the command to change the
DPI settings on the PMW3320DB-TYDU, but sending the full power up sequence with
a new DPI seems feasible.

I had wired the low/high DPI switch to the controller when 
[reassembling the EX-G]({% post_url 2026-02-09-ex-g-reassembly %}#using-the-ex-g-for-a-day). 
However, I did not test all the connections, only the ones I was using at the
time. With this in mind my plan is:

1. Write a simple Arduino sketch to verify the low/high DPI switch is wired up
   and functioning.
2. Add logic to send a power up reset when the low/high switch changes
   positions.

It's possible the switch isn't wired correctly and functioning. If that's the
case this will be a fairly short post...

# Testing the DPI Switch

An Arduino sketch that serial prints the switch's value when it changes
position will be used. 

Looking back at
[reassembling the EX-G]({% post_url 2026-02-09-ex-g-reassembly %}#using-the-ex-g-for-a-day)
the `MTMS` pin was connected to the DPI switch. The 
[ESP32S3](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/) getting
started website shows the `MTMS` pin is `GPIO42`. Thus `42` is the
[answer](https://simple.wikipedia.org/wiki/42_(answer)) and will be used in the
sketch.

There is a `Button` abstraction used for the left, right, and middle click
buttons. The test will use this abstraction for the DPI switch.

```c
#include "Button.hpp"
#include <optional>

std::optional<Button> dpiSwitch = {};

void setup() {
  Serial.begin();
  dpiSwitch.emplace(42);
}

void loop() {
  auto dpiState = dpiSwitch->stateChange();
  if(dpiState) {
    if (*dpiState == ButtonState::PRESSED) {
      Serial.println("pressed");
    } else {
      Serial.println("released");
    }
  }
}
```

Let's compile and run this...

```
pressed
released
pressed
released
pressed
released
```

Well that's nice. The button is wired up to pin 42 and it functions correctly.
The `pressed` output happens when the switch is moved to the high DPI position.
From the earlier posts on the EX-G, all of the buttons and switches are logical
`HIGH` when open. Since the switch outputs `pressed` when going to the high DPI
position, this means that it closed the connection and went logical `LOW`.

# Logicing the DPI Switch

The current code passes the DPI during the constructor of the sensor.
```c
  sensor.emplace(D7, 1500);
```
Passing the DPI via the constructor during power up still seems like an
ergonomic API. The code will need to be modified to read the state of the DPI
switch to determine which value to pass. I'll add some constants and a define
for the pin number.

```c
std::optional<Button> dpiSwitch;
const uint16_t lowDpi = 1500;
const uint16_t highDpi = 2000;
#define DPI_PIN 42

// later in setup()
  dpiSwitch.emplace(DPI_PIN);
  auto dpi = lowDpi;
  if(digitalRead(DPI_PIN) == LOW) {
    dpi = highDpi;
  }
  // D8, D9, D10 are SPI pins
  sensor.emplace(D7, dpi);
```
The `dpiSwitch` is created before the sensor. This ensures the pin is already
set up as an input before trying to read its state.

Compile and upload.

Plugging in the EX-G after the upload, with the DPI switch in the low DPI
position the EX-G seems to behave as it used to. Unplugging and moving the
switch to the high DPI settings, then plugging back in. It does seem like the
cursor is moving faster across the computer screen. A nice little step in the
right direction.


<details>
  <summary>ex-g.ino modified to power on with different DPIs</summary>
<div markdown="1">
{% raw %}
```c 
#include "Button.hpp"
#include "MotionSensor.hpp"
#include "ScrollWheel.hpp"
#include <USB.h>
#include <USBHIDMouse.h>
#include <optional>

USBHIDMouse Mouse;

struct MouseButton {
  uint8_t pin;
  uint8_t mouseButton;
  std::optional<Button> button;
};

enum MouseButtonIndex : uint8_t {
  LEFT = 0,
  RIGHT = 1,
  MIDDLE = 2,
};

// The USB mouse takes the entire serial pipe, which prevents uploading new
// software. To avoid needing to access the boot button on the board, this
// flag is used to skip the mouse logic, leaving the serial bus open.
// This is achieved by holding down left and right click while plugging in the
// device.
bool serialUploadMode = false;

std::optional<MotionSensor> sensor;
std::optional<ScrollWheel> scrollWheel;
MouseButton mouseButtons[] = {
    {D2, MOUSE_LEFT, {}},
    {D3, MOUSE_RIGHT, {}},
    {D4, MOUSE_MIDDLE, {}},
};

std::optional<Button> dpiSwitch;
const uint16_t lowDpi = 1500;
const uint16_t highDpi = 2000;
#define DPI_PIN 42

/**
 * @brief Check if LEFT and RIGHT are held low for 1 second to enable serial
 * upload mode.
 * @return true if both buttons were held low for the full duration.
 */
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

/**
 * @brief Called once at program startup to perform initialization.
 *
 * Place any hardware or application initialization code here; this function
 * is invoked once before the main execution loop begins.
 */
void setup() {
  serialUploadMode = checkSerialUploadMode();
  if (serialUploadMode) {
    return;
  }
  // Delay to allow time for the peripherals to power up
  delay(1000);

  Mouse.begin();
  USB.begin();
  dpiSwitch.emplace(DPI_PIN);
  auto dpi = lowDpi;
  if (digitalRead(DPI_PIN) == LOW) {
    dpi = highDpi;
  }
  // D8, D9, D10 are SPI pins
  sensor.emplace(D7, dpi);
  scrollWheel.emplace(D0, D1);
  for (auto &mb : mouseButtons) {
    mb.button.emplace(mb.pin);
  }
}

/**
 * @brief Executes repeatedly after setup to perform the sketch's main logic.
 *
 * This function is invoked in a continuous loop by the Arduino runtime; place
 * recurring or periodic code here. Currently the implementation is empty.
 */
void loop() {
  if (serialUploadMode) {
    return;
  }
  auto motion = sensor->motion();
  auto scroll = scrollWheel->delta();
  if (motion || scroll) {
    auto m = motion.value_or(Motion{0, 0});
    Mouse.move(m.delta_x, m.delta_y, scroll.value_or(0));
  }

  for (auto &mb : mouseButtons) {
    auto state = mb.button->stateChange();
    if (state) {
      if (*state == ButtonState::PRESSED) {
        Mouse.press(mb.mouseButton);
      } else {
        Mouse.release(mb.mouseButton);
      }
    }
  }
}
```
{% endraw %}
</div>
</details><br/>
The next step is looking at the DPI switch state in the `loop()`. This will
allow changing the DPI after power up, and more importantly do a full power up
reset of the PMW3320DB-TYDU. To do this a function needs to be added to the 
[MotionSensor](https://github.com/speedyleion/ex-g/blob/1f02d0631e31c69e4db4b586845e5bbb93af5add/MotionSensor.cpp).

```c++
void MotionSensor::setDpi(uint16_t dpi) {
  _resolution = dpiToRegisterValue(dpi);
  initPmw();
}
```

This function will take an input DPI, convert it to the appropriate register
value storing it in a member variable. Then it will call `initPmw()`,
re-initializing the PMW3320DB-TYDU. The function declaration will also need to
be added to the header.

Next the `loop()` will be modified to call this function with the appropriate
value when the switch changes.

```c
  auto dpiState = dpiSwitch->stateChange();
  if(*dpiState == ButtonState::PRESSED) {
    sensor->setDpi(highDpi);
  } else {
    sensor->setDpi(lowDpi);
  }
```

<details>
  <summary>ex-g.ino modified to monitor DPI switch</summary>
<div markdown="1">
{% raw %}
```c
#include "Button.hpp"
#include "MotionSensor.hpp"
#include "ScrollWheel.hpp"
#include <USB.h>
#include <USBHIDMouse.h>
#include <optional>

USBHIDMouse Mouse;

struct MouseButton {
  uint8_t pin;
  uint8_t mouseButton;
  std::optional<Button> button;
};

enum MouseButtonIndex : uint8_t {
  LEFT = 0,
  RIGHT = 1,
  MIDDLE = 2,
};

// The USB mouse takes the entire serial pipe, which prevents uploading new
// software. To avoid needing to access the boot button on the board, this
// flag is used to skip the mouse logic, leaving the serial bus open.
// This is achieved by holding down left and right click while plugging in the
// device.
bool serialUploadMode = false;

std::optional<MotionSensor> sensor;
std::optional<ScrollWheel> scrollWheel;
MouseButton mouseButtons[] = {
    {D2, MOUSE_LEFT, {}},
    {D3, MOUSE_RIGHT, {}},
    {D4, MOUSE_MIDDLE, {}},
};

std::optional<Button> dpiSwitch;
const uint16_t lowDpi = 1500;
const uint16_t highDpi = 2000;
#define DPI_PIN 42

/**
 * @brief Check if LEFT and RIGHT are held low for 1 second to enable serial
 * upload mode.
 * @return true if both buttons were held low for the full duration.
 */
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

/**
 * @brief Called once at program startup to perform initialization.
 *
 * Place any hardware or application initialization code here; this function
 * is invoked once before the main execution loop begins.
 */
void setup() {
  serialUploadMode = checkSerialUploadMode();
  if (serialUploadMode) {
    return;
  }
  // Delay to allow time for the peripherals to power up
  delay(1000);

  Mouse.begin();
  USB.begin();
  dpiSwitch.emplace(DPI_PIN);
  auto dpi = lowDpi;
  if (digitalRead(DPI_PIN) == LOW) {
    dpi = highDpi;
  }
  // D8, D9, D10 are SPI pins
  sensor.emplace(D7, dpi);
  scrollWheel.emplace(D0, D1);
  for (auto &mb : mouseButtons) {
    mb.button.emplace(mb.pin);
  }
}

/**
 * @brief Executes repeatedly after setup to perform the sketch's main logic.
 *
 * This function is invoked in a continuous loop by the Arduino runtime; place
 * recurring or periodic code here. Currently the implementation is empty.
 */
void loop() {
  if (serialUploadMode) {
    return;
  }
  auto motion = sensor->motion();
  auto scroll = scrollWheel->delta();
  if (motion || scroll) {
    auto m = motion.value_or(Motion{0, 0});
    Mouse.move(m.delta_x, m.delta_y, scroll.value_or(0));
  }

  for (auto &mb : mouseButtons) {
    auto state = mb.button->stateChange();
    if (state) {
      if (*state == ButtonState::PRESSED) {
        Mouse.press(mb.mouseButton);
      } else {
        Mouse.release(mb.mouseButton);
      }
    }
  }

  auto dpiState = dpiSwitch->stateChange();
  if(*dpiState == ButtonState::PRESSED) {
    sensor->setDpi(highDpi);
  } else {
    sensor->setDpi(lowDpi);
  }

}
```
{% endraw %}
</div>
</details>

<details>
  <summary>MouseSensor.cpp modified with set DPI function</summary>
<div markdown="1">
{% raw %}
```c++
#include "MotionSensor.hpp"
#include "SpiTransaction.hpp"
#include <Arduino.h>
#include <SPI.h>

// Based on https://www.espruino.com/datasheets/ADNS5050.pdf
const int tWakeup = 55;

// This time was re-used from capture taken for OEM EX-G initializing
// PMW3320DB-TYDU
const int tPowerUpCs = 2;

// Time between commands, in µs
//
// Based on https://www.espruino.com/datasheets/ADNS5050.pdf
// worst case is tsww at 30 µs, which is time from last bit of first byte to
// last bit of second byte. At max speed of, 1,000,000 Hz 8 bits would take 8 µs
// leaving a pause of 22 µs.
//
// The data sheet also mentions
//
//    SCLK to NCS Inactive, tSCLK-NCS, 20 µs from last SCLK rising edge to NCS
//    (for write operation) rising edge, for valid SDIO data transfer.
//
// This seems to imply that we need 20 μs before moving chip select back high,
// so we'll cheat and re-use this value of 22 (for now?)
const int tWus = 22;

const int IDLE_READ = 0x00;

// Register addresses from
// https://www.epsglobal.com/Media-Library/EPSGlobal/Products/files/pixart/PMW3320DB-TYDU.pdf
const int PROD_ID = 0x00;
const int POWER_UP_RESET = 0x3A;
const int PERFORMANCE = 0x22;
const int RESOLUTION = 0x0D;
const int AXIS_CONTROL = 0x1A;
const int BURST_READ_FIRST = 0x42;
const int MOTION = 0x02;
const int DELTA_X = 0x03;
const int DELTA_Y = 0x04;
const int BURST_MOTION = 0x63;

// As specified in
// https://www.epsglobal.com/Media-Library/EPSGlobal/Products/files/pixart/PMW3320DB-TYDU.pdf
const int MAX_DPI = 3500;
const int DPI_RESOLUTION = 250;
const int MAX_CLOCK_SPEED = 1'000'000;

/**
 * @brief Construct a MotionSensor and configure SPI and sensor hardware.
 *
 * Initializes SPI with the provided SCK/CIPO/COPI pins, applies SPI settings
 * (1 MHz, MSB first, mode 3), stores the chip-select pin, and runs the PMW
 * sensor initialization sequence.
 *
 * @param cs Chip-select pin connected to the sensor.
 * @param dpi Sensor DPI value (logical configuration; may be used elsewhere).
 * @param sck Serial clock pin (SCLK).
 * @param cipo Controller-In-Peripheral-Out pin (CIPO).
 * @param copi Controller-Out-Peripheral-In pin (COPI).
 */
MotionSensor::MotionSensor(int8_t cs, uint16_t dpi, int8_t sck, int8_t cipo,
                           int8_t copi) {
  SPI.begin(sck, cipo, copi);
  _settings = SPISettings(MAX_CLOCK_SPEED, SPI_MSBFIRST, SPI_MODE3);
  _cs = cs;
  _resolution = dpiToRegisterValue(dpi);

  pinMode(_cs, OUTPUT);
  digitalWrite(_cs, HIGH); // Deselect initially
  initPmw();
}

std::optional<Motion> MotionSensor::motion() {
  uint8_t motion_reg;
  int8_t delta_x;
  int8_t delta_y;
  {
    SpiTransaction transaction(_cs, _settings);
    SPI.transfer(BURST_MOTION);
    delayMicroseconds(tWus);
    motion_reg = SPI.transfer(IDLE_READ);
    delayMicroseconds(tWus);
    delta_y = (int8_t)SPI.transfer(IDLE_READ);
    delayMicroseconds(tWus);
    delta_x = -(int8_t)SPI.transfer(IDLE_READ);
    delayMicroseconds(tWus);
  }
  if (motion_reg & 0x80) {
    return Motion{delta_x, delta_y};
  }
  return std::nullopt;
}

void MotionSensor::setDpi(uint16_t dpi) {
  _resolution = dpiToRegisterValue(dpi);
  initPmw();
}

uint8_t MotionSensor::dpiToRegisterValue(uint16_t dpi) {
  if (dpi < DPI_RESOLUTION) {
    dpi = DPI_RESOLUTION;
  }
  if (dpi > MAX_DPI) {
    dpi = MAX_DPI;
  }
  uint16_t steps = (dpi + (DPI_RESOLUTION / 2)) / DPI_RESOLUTION;
  return (uint8_t)steps;
}

/**
 * @brief Initializes the PMW/ADNS optical sensor and configures its operating
 * registers.
 *
 * Performs the required chip-select wake/power-up sequence and executes the
 * sensor initialization register sequence to reset the device, configure
 * performance and resolution, set axis control, and enable burst/motion
 * reporting.
 */
void MotionSensor::initPmw() {
  // Drive High and then low from
  // https://media.digikey.com/pdf/data%20sheets/avago%20pdfs/adns-3050.pdf
  digitalWrite(_cs, LOW);
  digitalWrite(_cs, HIGH);
  delay(tPowerUpCs);
  digitalWrite(_cs, LOW);
  delay(tPowerUpCs);

  delay(tWakeup);

  write(POWER_UP_RESET, 0x5A);
  // The OEM software read this value, copying the behavior to be safe
  read(PROD_ID);
  write(PERFORMANCE, 0x80);
  // These registers are unknown. They were observed to be written to by the OEM
  // EX-G software,
  // https://speedyleion.github.io/mice/electronics/2026/01/11/ex-g-pmw3320db-tydu-spi-traffic.html
  write(0x1D, 0x0A);
  write(0x14, 0x40);
  write(0x18, 0x40);
  write(0x34, 0x28);
  write(0x64, 0x32);
  write(0x65, 0x32);
  write(0x66, 0x26);
  write(0x67, 0x26);
  write(0x21, 0x04);
  write(PERFORMANCE, 0x00);
  // The resolution for the PMW3320DB-TYDU is documented as a max of 3500 DPI
  // with a 250 DPI resolution. Observing the OEM EX-G software a value of 0x83
  // was sent for 750 DPI, and a value of 0x86 was sent for a value of 1500 DPI
  // It seems that the MSB needs to be set, and that the LSB's represent the DPI
  // value. 3500/250 = 14 or 0x0D so this is likely 0x81-0x8D
  write(RESOLUTION, 0x80 | _resolution);
  // The OEM software read the value before writing, copying the behavior to be
  // safe
  read(AXIS_CONTROL);
  // The 0XA0 value was observed from the OEM EX-G software. It's likely
  // specific to the physical orientation of the sensor in the case.
  write(AXIS_CONTROL, 0xA0);
  write(BURST_READ_FIRST, 0x02);

  // The OEM software read these. I'm thinking it's likely to ensure they're
  // cleared.
  read(MOTION);
  read(DELTA_X);
  read(DELTA_Y);
}

/**
 * @brief Writes a byte to a sensor register over SPI.
 *
 * @param reg Sensor register address to write to.
 * @param value Data byte to write into the register.
 */
void MotionSensor::write(uint8_t reg, uint8_t value) {
  SpiTransaction transaction(_cs, _settings);
  SPI.transfer((uint8_t)(0x80 | reg));
  delayMicroseconds(tWus);
  SPI.transfer(value);
  delayMicroseconds(tWus);
}

/**
 * @brief Read a single byte from a PMW/ADNS sensor register over SPI.
 *
 * Selects the sensor, issues a read for the given register address, and returns
 * the byte read from that register.
 *
 * @param reg Register address to read.
 * @return uint8_t The byte value read from the specified register.
 */
uint8_t MotionSensor::read(uint8_t reg) {
  SpiTransaction transaction(_cs, _settings);
  SPI.transfer(reg);
  delayMicroseconds(tWus);
  uint8_t ret_value = SPI.transfer(IDLE_READ);
  delayMicroseconds(tWus);
  return ret_value;
}
```
{% endraw %}
</div>
</details><br/>
Compile and upload.

When trying to use the trackball the cursor doesn't move. Toggling the DPI
switch between low and high seems to have no effect. The scroll wheel works.
The left, right and middle click buttons work. Everything but the trackball
works.

I've been heads down for a bit, it's probably time to go for a walk.

## Debugging the Cursor Freeze

An hour later, and I'm back to take another crack. The main difference is I'm
calling the `initPmw()` in a place I hadn't before. Scrutinizing that function I'm
not seeing anything that stands out. The chip select is forced `HIGH` in the
constructor of the `MouseSensor`. Looking inside `initPmw()`, it uses the 
[SpiTransaction](https://github.com/speedyleion/ex-g/blob/1f02d0631e31c69e4db4b586845e5bbb93af5add/SpiTransaction.hpp)
which will activate and de-activate the chip select as necessary.

It may be time to see what the new AI overlords have to say. It quickly points
out the error:
```c
  auto dpiState = dpiSwitch->stateChange();
  if(*dpiState == ButtonState::PRESSED) {
    sensor->setDpi(highDpi);
  } else {
    sensor->setDpi(lowDpi);
  }
```
The code that is keying off the `dpiState` is wrong. It should be:
```c
  auto dpiState = dpiSwitch->stateChange();
  if (dpiState) {
    if (*dpiState == ButtonState::PRESSED) {
      sensor->setDpi(highDpi);
    } else {
      sensor->setDpi(lowDpi);
    }
  }
```
It was improperly dereferencing the `dpiState` without making sure that the
`dpiState` contained a valid value. Since it was an if/else condition the code
was always calling `setDpi()` with either the `highDpi` or the `lowDpi` value.
The PMW3320DB-TYDU was in a constant state of reset, so any track ball movement
was always getting cleared.

Compile and upload.

This works! Moving the DPI switch to high results in noticeably faster cursor
movement. Moving to low provides the cursor speed I've been used to.

# A Day Later

While the code could use some cleanup, I ran out of time so went with the
current implementation and used it most of the day. On starting the day I got
the problem where the trackball didn't seem to be tracking fine movement again.
This was the problem I wanted the power up reset for. So I moved the DPI switch
to high and went to use the trackball. It still lacked fine movement in one
direction. I toggled back to low to try and force the reset again. Still lacking
fine movement in one direction.

I realized that in the weeks prior I had plugged the trackball into a USB port on
the front of my docking station. This time I plugged it into a port on the back
of the docking station. Moving the USB cable back to the front of the docking
station remedied the situation...

Looking at the port on the back it's a thunderbolt port. I don't know much about
the differences between the ports, but I thought that USB would work on these
ports just fine, why else would they make them the same connector.

# Summary

It looks like my hypothesis about slow power up causing loss of fine precision
at times, was incorrect. Thinking about it more, when I had first encountered
this issue it was likely plugged into the back port and I had plugged it into
the front one as it was easy to do repeatedly if needed.

I probably need to find some time to understand the real differences between
thunderbolt and USB.

I now have the capability to toggle the DPI with the hardware switch. I want to
clean up the code though. I likely want a dedicated class for the DPI switch. It
feels a bit clunky to look for `LOW` and then set the DPI to high. It also feels
awkward to look for `Pressed` when it's a toggle switch not a push button.

The `MotionSensor` could use some rework. The `_resolution` member variable was
questionable before and isn't an ideal way to communicate the value to use in
the register. Instead `initPmw()` should likely take that value as an argument.


