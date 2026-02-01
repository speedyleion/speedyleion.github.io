---
layout: post
title:  "Seeed Studio XIAO ESP32S3 Trackball Motion"
date:   2026-02-01 11:00:03 -0800
categories: mice electronics arduino
---

It was discovered, in the post
[Failing to Control the PMW3320DB-TYDU with SPI]({% post_url 2026-01-18-esp32c6-spi-pmw3320db-tydu %}),
that the ESP32C6 doesn't support HID emulation. HID (Human Interface Device)
support is necessary to act as a mouse or trackball. I was able to determine
that the
[ESP32S3](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/) does
support HID. So I switched the board I'm using for development from the ESP32C6
to the ESP32S3. Being the same family of chips, I was able to leverage 
learnings from 
[Seeed Studio XIAO esp32c6]({% post_url 2026-01-12-seeed-studio %}),
substituting most instances of `C6` for `S3`.

The ESP32 core libraries provide the HID support and code for use with the
ESP32S3. This means no extra libraries are needed. Initializing and sending
mouse commands is slightly different than the Arduino Mouse library. An 
[example](https://github.com/espressif/arduino-esp32/blob/master/libraries/USB/examples/Mouse/ButtonMouseControl/ButtonMouseControl.ino)
is provided in the Espressif GitHub repo.

The ESP32S3 mouse logic requires a `USBHIDMouse` object. `USBHIDMouse::begin()`
and `USB::begin()` need to be called in the `setup()` function.

```c
#include "USB.h"
#include "USBHIDMouse.h"
USBHIDMouse Mouse;
void setup() {
  // ... other setup code
  Mouse.begin();
  USB.begin();
}
```

The other functions, `move()`, `press()`, `release()`, and `click()`, behave
the same as their Arduino Mouse library counterparts.

# Finalizing the Trackball Motion Code

I had previously written about my 
[Code Plan for Wired EX-G Trackball]({% post_url 2026-01-28-code-plan-for-ex-g %}).
I've since started to implement the code in a GitHub repository,
[ex-g](https://github.com/speedyleion/ex-g/blob/361f5d6a1fc16f5b7e869f0d565cb08a9bd0fdb8).

The code currently consists of four source files:
<ul>
<li><details>
  <summary><a href="https://github.com/speedyleion/ex-g/blob/361f5d6a1fc16f5b7e869f0d565cb08a9bd0fdb8/SpiTransaction.hpp">SpiTransaction.hpp</a></summary>
<div markdown="1">
{% raw %}
```cpp
#ifndef SPI_TRANSACTION_HPP
#define SPI_TRANSACTION_HPP

#include <Arduino.h>
#include <SPI.h>

/**
 * @brief RAII wrapper for SPI transactions with chip-select control.
 *
 * Manages the lifecycle of an SPI transaction by beginning the transaction
 * and asserting chip-select LOW on construction, then releasing chip-select
 * HIGH and ending the transaction on destruction. This ensures proper cleanup
 * even when exceptions occur or early returns are taken.
 */
class SpiTransaction {
public:
  /**
   * @brief Begin an SPI transaction and assert chip-select.
   *
   * @param cs Chip-select pin to drive LOW for the duration of the transaction.
   * @param settings SPI configuration (clock speed, bit order, mode).
   */
  SpiTransaction(int8_t cs, SPISettings &settings) : _cs(cs) {
    SPI.beginTransaction(settings);
    digitalWrite(_cs, LOW);
  }

  /**
   * @brief End the SPI transaction and release chip-select.
   *
   * Drives the chip-select pin HIGH and calls SPI.endTransaction().
   */
  ~SpiTransaction() {
    digitalWrite(_cs, HIGH);
    SPI.endTransaction();
  }

  SpiTransaction(const SpiTransaction &) = delete;
  SpiTransaction &operator=(const SpiTransaction &) = delete;

private:
  int8_t _cs;
};

#endif
``` 
{% endraw %}
</div>
</details></li>
<li><details>
  <summary><a href="https://github.com/speedyleion/ex-g/blob/361f5d6a1fc16f5b7e869f0d565cb08a9bd0fdb8/MotionSensor.hpp">MotionSensor.hpp</a></summary>
<div markdown="1">
{% raw %}
```cpp
#ifndef MOTION_SENSOR_HPP
#define MOTION_SENSOR_HPP
#include <Arduino.h>
#include <SPI.h>
#include <cstdint>
#include <optional>
#include <ostream>

struct Motion {
  int8_t delta_x;
  int8_t delta_y;

  bool operator==(const Motion &other) const {
    return delta_x == other.delta_x && delta_y == other.delta_y;
  }

  friend std::ostream &operator<<(std::ostream &os, const Motion &m) {
    return os << "{dx=" << (int)m.delta_x << ", dy=" << (int)m.delta_y << "}";
  }
};

// MotionSensor
class MotionSensor {
public:
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
  MotionSensor(int8_t cs, uint16_t dpi, int8_t sck = -1, int8_t cipo = -1,
              int8_t copi = -1);
  /**
   * @brief Get the motion since the last time motion was retrieved
   *
   * Returns the motion values from the sensor if available.
   */
  std::optional<Motion> motion();

private:
  SPISettings _settings;
  int8_t _cs;
  // DPI resolution in register units
  uint8_t _resolution;
  void initPmw();

  // public for ease of testing
public:
  uint8_t read(uint8_t reg);
  void write(uint8_t reg, uint8_t value);
  static uint8_t dpiToRegisterValue(uint16_t dpi);
};
#endif // MOTION_SENSOR_HPP
``` 
{% endraw %}
</div>
</details></li>
<li><details>
  <summary><a href="https://github.com/speedyleion/ex-g/blob/361f5d6a1fc16f5b7e869f0d565cb08a9bd0fdb8/MotionSensor.cpp">MotionSensor.cpp</a></summary>
<div markdown="1">
{% raw %}
```cpp
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
    delta_x = (int8_t)SPI.transfer(IDLE_READ);
    delayMicroseconds(tWus);
    delta_y = (int8_t)SPI.transfer(IDLE_READ);
    delayMicroseconds(tWus);
  }
  if (motion_reg & 0x80) {
    return Motion{delta_x, delta_y};
  }
  return std::nullopt;
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
</details></li>
<li><details>
  <summary><a href="https://github.com/speedyleion/ex-g/blob/361f5d6a1fc16f5b7e869f0d565cb08a9bd0fdb8/ex-g.ino">ex-g.ino</a></summary>
<div markdown="1">
{% raw %}
```c
#include "MotionSensor.hpp"
#include <USB.h>
#include <USBHIDMouse.h>
#include <optional>

USBHIDMouse Mouse;
std::optional<MotionSensor> sensor;
/**
 * @brief Called once at program startup to perform initialization.
 *
 * Place any hardware or application initialization code here; this function
 * is invoked once before the main execution loop begins.
 */
void setup() {
  Mouse.begin();
  USB.begin();
  sensor.emplace(D7, 1500);
}

/**
 * @brief Executes repeatedly after setup to perform the sketch's main logic.
 *
 * This function is invoked in a continuous loop by the Arduino runtime; place
 * recurring or periodic code here. Currently the implementation is empty.
 */
void loop() {
  auto motion = sensor->motion();
  if (motion) {
    Mouse.move(motion->delta_x, motion->delta_y);
  }
}
``` 
{% endraw %}
</div>
</details></li>
</ul>

> Hint: expand any of the above to see the code.

## SpiTransaction.hpp

This file wasn't in the 
[Code Plan for Wired EX-G Trackball]({% post_url 2026-01-28-code-plan-for-ex-g %}).
A couple of things happened that had me create this:
1. I was using [coderabbit.ai](https://www.coderabbit.ai/), it provided a review
   comment indicating that my implementation of activating the SPI chip select
   prior to beginning the SPI transaction was not recommended.
2. I realized the ending of the transaction, as well as deactivating the chip
   select would be more ergonomic using
   [RAII](https://en.wikipedia.org/wiki/Resource_acquisition_is_initialization).

The `SPI.beginTransaction()` and `SPI.endTransaction()` are used to ensure
isolation in case there are multiple threads using SPI. This prevents one
thread from trying to communicate using SPI, while another thread is in the
process. The logic I had before, which activated the chip select line prior to
`SPI.beginTransaction()`, could result in one thread activating the chip select
line to start communicating, while another thread was finishing up. The other
thread might deactivate the chip select line, thus negating the other thread's
communication. 

The `SPI.beginTransaction()` and `SPI.endTransaction()` calls act as a critical
section where only one thread should be interacting with SPI. Thus all
SPI-specific commands should be within these calls.

To provide better ergonomics and make it less error prone, I decided to leverage
RAII. This uses a dedicated class that starts the transaction in the class
constructor and ends the transaction in the class destructor.

An example usage would look something like the following:
```cpp
void foo() {
  SpiTransaction transaction(cs, settings);
  // ... SPI messages

  // RAII will deactivate chip select and end 
  // SPI when `transaction` leaves scope
}
```



## MotionSensor.hpp

This is the header file for MotionSensor.cpp. Being written in C++ the header
files are more or less implied if one wants to write the implementation in a
dedicated `*.cpp` file.

## MotionSensor.cpp

This is the main part of the logic that talks to the 
[PMW3320DB-TYDU]({% post_url 2025-12-31-pmw3320db-tydu-sensor %}).
This logic is similar to the prototype code used in 
[Failing to Control the PMW3320DB-TYDU with SPI]({% post_url 2026-01-18-esp32c6-spi-pmw3320db-tydu %}).
Instead of a `setup()` the initialization of the SPI and PMW3320DB-TYDU happens
in the constructor.

The function for getting any potential trackball movement is called `motion()`.
It leverages the burst read capability of the PMW3320DB-TYDU, instead of reading
one register at a time. I was able to use
[std::optional](https://en.cppreference.com/w/cpp/utility/optional.html) for the
return type, as hoped for in my initial code plan.

## ex-g.ino

`ex-g.ino` is the primary sketch. It provides the `setup()` and `loop()` logic.
Removing comments and blank lines we can see how thin this file is, right now.
```c
#include "MotionSensor.hpp"
#include <USB.h>
#include <USBHIDMouse.h>
#include <optional>
USBHIDMouse Mouse;
std::optional<MotionSensor> sensor;
void setup() {
  Mouse.begin();
  USB.begin();
  sensor.emplace(D7, 1500);
}
void loop() {
  auto motion = sensor->motion();
  if (motion) {
    Mouse.move(motion->delta_x, motion->delta_y);
  }
}
```
For comparison, one can look again at the code in 
[Failing to Control the PMW3320DB-TYDU with SPI]({% post_url 2026-01-18-esp32c6-spi-pmw3320db-tydu %}).
There was significantly more logic happening within the sketch itself. Now a
large portion of that logic has been moved out to `MotionSensor.cpp`, keeping
`ex-g.ino` focused on the higher level idea of polling for motion and sending
that motion as mouse movement.

Since the `MotionSensor` object will initialize SPI and the PMW3320DB-TYDU
during construction, it can't be constructed outside of `setup()`. Until now, I
didn't understand the partial construction that other Arduino classes use. For
instance, the `USBHIDMouse` is constructed empty. When its `begin()` is called,
it becomes fully initialized. In order to work around this with the
`MotionSensor`, I use a `std::optional` that will be constructed using the
default
[std::nullopt](https://en.cppreference.com/w/cpp/utility/optional/nullopt). In
the `setup()` it's replaced with a `MotionSensor` instance, the
`sensor.emplace()` call.

The `loop()` is fairly simple in that it polls for `motion` and if the
`std::optional` has a value it calls `Mouse::move()` with the values.

# ESP32S3 with Physical Trackball

I repeated similar steps as the
[Second Attempt to Control the PMW3320DB-TYDU with SPI]({% post_url 2026-01-20-esp32c6-spi-pmw3320db-tydu-take-two %})
for the physical connections between the ESP32S3 and the PMW3320DB-TYDU. I was
able to compile and upload the code to the ESP32S3. Once uploaded, the mouse
cursor on my computer started to slowly drift toward the upper left corner. I
tried moving the trackball to see if there was something lingering. The cursor
jumped sporadically across the screen. My heart sank...

I began to re-review all the code I had written for what might be causing stray
values to show up. Nothing seemed to stand out as an obvious mistake. The next
step was to comment out the `Mouse` and `USB` calls in `ex-g.ino` and replace
them with serial print statements like was done in 
[Second Attempt to Control the PMW3320DB-TYDU with SPI]({% post_url 2026-01-20-esp32c6-spi-pmw3320db-tydu-take-two %}).

I went to compile and upload the serial print version. It compiled fine, but
couldn't find the device to upload. I realized that the mouse cursor wasn't
moving any more either. I had unplugged the ESP32S3 from my computer when the
mouse cursor had gone awry, to make the code changes. I re-connected it to my
computer to upload the new changes, but now the mouse cursor wasn't moving. I
reached over and moved the trackball, it moved the cursor as expected!

It appears that the ESP32S3 doesn't support concurrent serial and HID across the
USB interface. In order to get the ESP32S3 to show up again as a serial device I
needed to hold down the boot button while plugging it in. Once plugged in, the
button can be released and the ESP32S3 will show up again as an available serial
device.

I think what likely happened, is when I first uploaded the trackball motion
code, the ESP32S3 was still trying to use the serial connection and the new HID
logic on the same USB connection. The serial connection resulted in noise in the
HID connection. I'm not sure, though. I don't have a good enough understanding
of the interfaces to say for sure. What I do know is that I will be unplugging
the ESP32S3 after future uploads before testing behavior.

