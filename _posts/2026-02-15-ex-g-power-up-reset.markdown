---
layout: post
title:  "EX-G Power Up Reset"
date:   2026-02-15 12:00:03 -0800
categories: mice electronics arduino
---

There have been a few times where the wired version of the 
[EX-G](https://elecomusa.com/products/ex-g-trackball-wireless-usb-copy),
I [created]({% post_url 2026-02-09-ex-g-reassembly %}), lacks fine precision
movement of the trackball, in one or two axes. This occurs after a fresh power
up of the computer it's attached to. Unplugging the EX-G and plugging it back in
will result in the fine precision movement of the trackball working again. 

This issue was first encountered after 
[using the EX-G for a day]({% post_url 2026-02-09-ex-g-reassembly %}#using-the-ex-g-for-a-day). 
A workaround had been attempted, but after a few more days of use the
workaround has proven to be insufficient. The workaround entailed delaying the
power up reset cycle of the 
[PMW3320DB-TYDU](https://www.epsglobal.com/Media-Library/EPSGlobal/Products/files/pixart/PMW3320DB-TYDU.pdf)
for one second after the
[ESP32S3](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/) controller
started up. The one second delay wasn't specifically for the loss of fine
precision movement. The delay was originally due to some of the PMW3320DB-TYDU
settings not persisting after power up. 

To mitigate the current issue, I could further increase the delay. This would
require trying to find the time it may take for the PMW3320DB-TYDU, through the
ESP32S3, to get sufficient power to maintain the power up settings. I already
felt like the one second delay was a bit of a hack. One second has a potential
to be noticeable to the trackball user. Adding more time feels like it's
likely to have negative usability effects.

The original wireless EX-G trackball will perform a full power up reset of the
PMW3320DB-TYDU optical sensor when it is toggled from low power to high power or
vice versa. This was discovered when 
[inspecting PMW3320DB-TYDU SPI with a logic analyzer]({% post_url 2026-01-03-logic-analyzer-pmw3320db-tydu %}).
This means that the power up reset could be performed at any time on the
PMW3320DB-TYDU, even after it's been powered up and had been used for reading
motion values.

# Potential Solutions

Thinking about the problem some, the trackball functions, but in a degraded
state, where the fine movements are difficult to perform. The power up shouldn't
be delayed for too long. The short delay is to ensure a user can use the
trackball _soon_ after plugging it in. The trackball shouldn't require multiple
attempts of unplugging and plugging back in to get to the ideal functioning
state. Given the preceding requirements, a likely solution involves forcing a
power up reset of the PMW3320DB-TYDU sensor when it's in this degraded state.

I'm not sure there is a programmatic way to know that the PMW3320DB-TYDU is in
this degraded state. The user definitely knows, but the values coming back from
the PMW3320DB-TYDU don't have a way to communicate if the user is doing fine
movement, or if the trackball doesn't happen to be moving along an axis.

My initial thought was to add some logic that would check for a period of no
motion. When this no motion, or idle, period happened the power up reset would
be invoked as a preventative measure. I'm not fond of the idea. It's one thing
to poll for state change, it's another to periodically set _unchanging_ state.

Most of the times I've encountered code that is continually setting _unchanging_
state, it seems to introduce more problems than it fixes. The state is
constantly being set to `X`, `Y`, and `Z`. Something else decides that instead
of `Y` the value should be `B`, so it makes a call to set the value to `B`. Then
the periodic update comes along and sets it back to `X`, `Y`, and `Z`. One could
design the periodic updater to have dynamic values that other elements could
call into to change what values the updater uses. In the end it often seems like
one starts to build software around the periodic update mechanism instead of
focusing on the underlying problem: the state should be `Y` under certain
conditions and `B` under other conditions. A periodic updater is a
code smell.

Slight tangent; re-reading "introduce more problems than it fixes" brings back
a memory. I used to be a mechanic, mostly working on construction equipment. We
were being given a training from the manufacturer on a new piece of equipment.
The instructor was getting close to retirement. In one of the earlier
presentations the instructor said "You all fuck-up more than you fix-up". That
stuck with me. Not because it was wrong, one could debate the "more" part, but
because some of the most memorable engineering and implementation scars are from
myself, or someone else, trying to make things better and doing the opposite.

Back on topic.

While writing this post I realized I could leverage the low/high DPI switch of
the EX-G. When it switches positions, it would send the power up reset. I could
even bring back a low and high DPI setting that the original EX-G had. This may
work fairly well. It requires user intervention, but lacking a programmatic way
to identify the degraded situation, the eventual solution may require some user
intervention. 

The approach I'm planning on taking was one of those shower thought solutions.
It came to me while actually taking a shower, my hair is probably not as clean
as it should be because of it.

Trackballs, as their name implies, use a physical ball to detect motion. Early
mice also used a ball to detect motion. Anyone who used those early mice recalls
having to pop the ball out of the mouse and clean the rollers that tracked the
ball's movement. Any trackball owner will know that trackballs suffer a similar
maintenance burden. Users of trackballs often need to clean the ball pit. Most
trackballs feature a hole on the bottom side where a user can push the ball out
with their pinky. This exposes the ball pit for cleaning.

I'm not sure if "ball pit" is a common term for it. I probably heard or read it
somewhere. If it isn't used anywhere, I'm totally taking credit for the term.

Anytime a user feels that the trackball isn't running smoothly or tracking
correctly, their first response is to clean the ball pit. My plan is to leverage
this cleaning time to trigger a power up reset. Using the cleaning time to
trigger the reset aligns with the actions a user is likely to take when the
trackball is misbehaving. While it's not the ideal automatic correction, it's
not a correction that requires the user to know something else about the device
to invoke.

The PMW3320DB-TYDU provides a burst read of register values. The current code
starts at the `MOTION` register, reads it, and the next two registers which are
`DELTA_X` and `DELTA_Y`. The register after `DELTA_Y` is `SQUAL`, which stands
for "surface quality". The PMW3320DB-TYDU doesn't say much about `SQUAL`, but
its sibling sensor the
[ADNS-3050](https://media.digikey.com/pdf/data%20sheets/avago%20pdfs/adns-3050.pdf)
says:

> SQUAL is nearly equal to zero, if there is no surface below the sensor

My understanding is that when the ball is removed from the housing the `SQUAL`
value will likely be 0 or close to it. This low value can be an indicator that
the trackball is currently being cleaned.

# The Plan

The plan is to create a cleaning mode state in the current
[MotionSensor.cpp](https://github.com/speedyleion/ex-g/blob/1f02d0631e31c69e4db4b586845e5bbb93af5add/MotionSensor.cpp).
When the cleaning mode state ends, a power up reset will be initiated for the
PMW3320DB-TYDU. All of the code changes will be made to the 
[ex-g repository](https://github.com/speedyleion/ex-g/blob/1f02d0631e31c69e4db4b586845e5bbb93af5add).

Steps:

1. Record how long the current power up reset instructions take to execute.
2. Expand the MotionSensor read to include the `SQUAL` register
3. Capture standard `SQUAL` values
    a. The ball in the housing
    b. The ball removed
4. Add state tracking logic to MotionSensor to know when it's in cleaning mode.
    a. Initialize MotionSensor in cleaning mode
    b. When `SQUAL` reaches the ball in housing value send power up reset

I want to know how long the power up reset takes to execute. I could compute
this, but it will be simpler to time it in code. This value helps to determine
when and where the power up reset can be done with limited impact to the user.

Adding the `SQUAL` to the burst read registers will be fairly cheap, since it's
the next register. The sensor is generic for mice or trackballs, so I doubt it
was next in burst specifically to handle trackball cleaning mode. However, it's
likely used in mice implementations to stop trying to send values when the user
picks the mouse up off the desk for any reason. 

In order to best determine when cleaning mode is done, I'll need to understand
the current `SQUAL` values. My thought is to print the time and the `SQUAL`
value, any time there is a change. This will hopefully keep the noise down and
give me an idea of the common values.

State tracking for cleaning mode will help mitigate spamming the reset to the
PMW3320DB-TYDU. I doubt there's any harm that could be had from constantly
sending the reset while the ball is removed. It just seems a bit clunky to be
constantly repeating the reset message, when it's not useful until the ball has
been replaced. This, unfortunately, means there must be some kind of state
tracking in place to know that the `MouseSensor` was in cleaning mode the last
time it was polled for motion.

# Power Up Reset Time

The timing for power up will be printed out using the ESP32S3's serial
interface. The ESP32S3 doesn't support serial print and `Mouse` output
concurrently through the USB port. This means the `Mouse` behavior will need to
be commented out for capturing the power up time.

<details>
  <summary>ex-g.ino modified to disable Mouse library</summary>
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
 */
void setup() {
  serialUploadMode = checkSerialUploadMode();
  if (serialUploadMode) {
    return;
  }
  // Delay to allow time for the peripherals to power up
  delay(1000);

  // Mouse.begin();
  // USB.begin();
  // D8, D9, D10 are SPI pins
  sensor.emplace(D7, 1500);
  scrollWheel.emplace(D0, D1);
  for (auto &mb : mouseButtons) {
    mb.button.emplace(mb.pin);
  }
  Serial.begin(115200);
}

/**
 * @brief Executes repeatedly after setup to perform the sketch's main logic.
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
        // Mouse.press(mb.mouseButton);
      } else {
        // Mouse.release(mb.mouseButton);
      }
    }
  }
}
```
{% endraw %}
</div>
</details>

Since the ESP32S3 was inside of the EX-G case, I wanted to be extra cautious
that I didn't break the `serialUploadMode` that's in the `ex-g.ino` file. If
this is broken then I will have a hard time uploading new code when the `Mouse`
library is active and using the USB.

The `MotionSensor.cpp` gets a fairly small change. The time prior to `initPmw()`
is recorded, then the time after. The difference between these two values is
printed.

The modified `MotionSensor` constructor looks like the following:

```cpp
MotionSensor::MotionSensor(int8_t cs, uint16_t dpi, int8_t sck, int8_t cipo,
                           int8_t copi) {
  SPI.begin(sck, cipo, copi);
  _settings = SPISettings(MAX_CLOCK_SPEED, SPI_MSBFIRST, SPI_MODE3);
  _cs = cs;
  _resolution = dpiToRegisterValue(dpi);

  pinMode(_cs, OUTPUT);
  digitalWrite(_cs, HIGH); // Deselect initially
  unsigned long start = millis();                                     
  initPmw();
  unsigned long end = millis();                                     
  Serial.print("Power Up Reset time: ");
  Serial.println(end - start);
}
```

With both files modified, they can be compiled and uploaded to the EX-G. The
EX-G is currently working as a trackball across the USB. To upload new software
the left and right click buttons need to be held down for one second while
plugging it in. I'll need to compile and upload the code.
```
arduino-cli compile --profile esp32s3 -u -p /dev/cu.usbmodem1401
```

Once uploaded I can see the serial output via the `monitor` subcommand of the
`arduino-cli`.

```
arduino-cli monitor -p /dev/cu.usbmodem1401 --fqbn esp32:esp32:XIAO_ESP32C6 --config 115200
```

All I get is the startup message from the command.

```
Monitor port settings:
  baudrate=115200
  bits=8
  dtr=on
  parity=none
  rts=on
  stop_bits=1

Connecting to /dev/cu.usbmodem1401. Press CTRL-C to exit.
```

I realize the print statements are happening in the `MotionSensor` constructor.
They're happening prior to `Serial.begin(115200)`. Even if the print statements
were happening after the call to `Serial.begin(115200)`. The `arduino-cli
monitor` will only be active while it actively sees a serial port. It's not
likely I could humanly connect the EX-G to my computer and start the
`arduino-cli` monitor between when the `Serial.begin(115200)` happens and when
the single call to `initPmw()` is made.

I think the easiest option is to make a call to `initPmw()` inside of the
`motion()` method.

```cpp
std::optional<Motion> MotionSensor::motion() {
  uint8_t motion_reg;
  int8_t delta_x;
  int8_t delta_y;
  unsigned long start = millis();                                     
  initPmw();
  unsigned long end = millis();                                     
  Serial.print("Power Up Reset time: ");
  Serial.println(end - start);
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
```

Compiling and uploading this produces a consistent output of:
```
Power Up Reset time: 61
Power Up Reset time: 61
Power Up Reset time: 61
```

It looks like it's 61 ms to power up. Seeing this value I'm immediately reminded
that I probably could have gotten this value from my work in 
[Inspecting PMW3320DB-TYDU SPI with Logic Analyzer]({% post_url 2026-01-03-logic-analyzer-pmw3320db-tydu %}).
Well I guess, I got some coding practice and reaffirmed how long it originally
took to do the power up reset, and how long it's currently taking.

# Read `SQUAL`

Reading the `SQUAL` register is a fairly small change. It involves making one
more `SPI.transfer()` call after reading the x and y values. I'll remove the
`initPmw()` print timings from the previous work.

```cpp
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
    uint8_t surfaceQuality = SPI.transfer(IDLE_READ);
    delayMicroseconds(tWus);
  }
  if (motion_reg & 0x80) {
    return Motion{delta_x, delta_y};
  }
  return std::nullopt;
}
```

As I write the code change, it begs the question if this was deserving of its
own step. It's not really beneficial until the next step when the value will be
printed, or the step after which will use this value to determine what state the
sensor is in.

# Outputting Surface Quality Values

I want to output the surface quality values, but only when they change. This way
I can better see the differences. If it was always printing I would get a wall of
text that would need to be manually parsed for duplicates. 

```cpp
std::optional<Motion> MotionSensor::motion() {
  static uint8_t surfaceQuality = 0;
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
    uint8_t newSurfaceQuality = SPI.transfer(IDLE_READ);
    delayMicroseconds(tWus);
    if (newSurfaceQuality != surfaceQuality) {
        Serial.print("Surface Quality: ");
        Serial.println(newSurfaceQuality);
        Serial.println(millis());
        surfaceQuality = newSurfaceQuality;
    }
  }
  if (motion_reg & 0x80) {
    return Motion{delta_x, delta_y};
  }
  return std::nullopt;
}
```

After compiling and uploading this modification I'll need to pop the ball out
and replace it to see the changes.

As I go to pick up the trackball assembly to remove the ball I start to see
output on the serial terminal.
```
Surface Quality: 14
246244
Surface Quality: 0
246244
Surface Quality: 15
246244
Surface Quality: 0
246245
Surface Quality: 14
246247
Surface Quality: 0
246247
```

Let me move the trackball and see what happens
```
Surface Quality: 15
287355
Surface Quality: 0
287356
Surface Quality: 14
287364
Surface Quality: 0
287364
Surface Quality: 240
287649
Surface Quality: 0
287649
Surface Quality: 240
287650
Surface Quality: 0
287650
```

That seems a bit odd. I expected that I might get some varying values when
moving the trackball. The 14 and 15 values happen when moving the trackball in
the motion that would move the cursor down on the screen. The 240 values happen
when moving the trackball as if to move the cursor up.

I remember the ADNS-3050 datasheet said the valid values are from 0-128. My
initial thought is that the 240 might be 15 with the most significant bit (MSB)
set. Since the MSB is outside the range of 128 this seems plausible. However,
thinking about it more, that doesn't seem correct. 240 in binary would be
`11110000` which would be 112 if the MSB was omitted.

The 0 values also seem odd. The output always ends in a 0. Looking at the code
it unconditionally prints the surface quality. While the delta x and y values
are only processed when motion has occurred. I think I should update the code to
only process the surface quality if there was motion.

```cpp
std::optional<Motion> MotionSensor::motion() {
  static uint8_t surfaceQuality = 0;
  uint8_t newSurfaceQuality;
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
    newSurfaceQuality = SPI.transfer(IDLE_READ);
    delayMicroseconds(tWus);
  }
  if (motion_reg & 0x80) {
    if (newSurfaceQuality != surfaceQuality) {
        Serial.print("Surface Quality: ");
        Serial.println(newSurfaceQuality);
        Serial.println(millis());
        surfaceQuality = newSurfaceQuality;
    }
    return Motion{delta_x, delta_y};
  }
  return std::nullopt;
}
```
The output of this change is
```
Surface Quality: 14
24603
Surface Quality: 0
24604
Surface Quality: 14
24605
Surface Quality: 0
24607
Surface Quality: 15
24608
Surface Quality: 14
24614
```
I still get zeros, but it doesn't always end with them and they're not always
right after a value. I think I need to dig into the surface quality docs of the
ADNS-3050 again.

Looking at the data type for the `SQUAL` register it has the following:

> Data Type: Upper 8 bits of a 9-bit unsigned integer.

Then later it mentions:

> the maximum SQUAL register value is 128.

I think what I'll do is left shift by 1 bit into a 16 bit value. Then take the
absolute value of this 16 bit value.

```cpp
std::optional<Motion> MotionSensor::motion() {
  static uint16_t surfaceQuality = 0;
  uint16_t newSurfaceQuality;
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
    newSurfaceQuality = abs(SPI.transfer(IDLE_READ) << 1);
    delayMicroseconds(tWus);
  }
  if (motion_reg & 0x80) {
    if (newSurfaceQuality != surfaceQuality) {
        Serial.print("Surface Quality: ");
        Serial.println(newSurfaceQuality);
        Serial.println(millis());
        surfaceQuality = newSurfaceQuality;
    }
    return Motion{delta_x, delta_y};
  }
  return std::nullopt;
}
```

The output seems odd still. The values still seem all over the place.

```
Surface Quality: 256
62874
Surface Quality: 30
62875
Surface Quality: 480
62876
Surface Quality: 30
62877
```
Looking more closely at my logic it's wrong. It never interprets the value as
signed.

```cpp
std::optional<Motion> MotionSensor::motion() {
  static uint16_t surfaceQuality = 0;
  uint16_t newSurfaceQuality;
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
    newSurfaceQuality = abs((int8_t)SPI.transfer(IDLE_READ) << 1);
    delayMicroseconds(tWus);
  }
  if (motion_reg & 0x80) {
    if (newSurfaceQuality != surfaceQuality) {
        Serial.print("Surface Quality: ");
        Serial.println(newSurfaceQuality);
        Serial.println(millis());
        surfaceQuality = newSurfaceQuality;
    }
    return Motion{delta_x, delta_y};
  }
  return std::nullopt;
}
```
That output looks better
```
Surface Quality: 30
30484
Surface Quality: 16
30486
Surface Quality: 32
30486
Surface Quality: 16
30489
Surface Quality: 32
30542
```

However I still get some output like
```
Surface Quality: 16
67191
Surface Quality: 0
67191
Surface Quality: 30
67195
Surface Quality: 0
67196
Surface Quality: 32
67994
Surface Quality: 0
67998
```
Playing with the trackball a bit, one thing I notice is that the times when I
get a zero every other value is the same direction that I was encountering
failures in precision movement. I wonder if it's related? I think what I'll do
is anytime I see the value zero I'll re-initialize the PMW3320DB-TYDU and see
what happens.

```cpp
std::optional<Motion> MotionSensor::motion() {
  static uint16_t surfaceQuality = 0;
  uint16_t newSurfaceQuality;
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
    newSurfaceQuality = abs((int8_t)SPI.transfer(IDLE_READ) << 1);
    delayMicroseconds(tWus);
  }
  if (motion_reg & 0x80) {
    if (newSurfaceQuality != surfaceQuality) {
        Serial.print("Surface Quality: ");
        Serial.println(newSurfaceQuality);
        Serial.println(millis());
        surfaceQuality = newSurfaceQuality;
        if(surfaceQuality == 0) {
            initPmw();
        }
    }
    return Motion{delta_x, delta_y};
  }
  return std::nullopt;
}
```

No change.
```
Surface Quality: 0
48036
Surface Quality: 32
48172
Surface Quality: 0
48200
Surface Quality: 30
48285
Surface Quality: 0
48298
```
I was hoping that re-initializing the PMW3320DB-TYDU would eliminate the 0
values. I'll have to think about this some. I'll likely end the post here and
try to come back again when I have some ideas for more investigations.


