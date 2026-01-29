---
layout: post
title:  "Code Plan for Wired EX-G Trackball"
date:   2026-01-28 18:00:03 -0800
categories: mice electronics arduino
---

<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true});</script>

At this point most of the pieces have come together for the wired EX-G
trackball. The main parts of the software have been prototyped:
- [mouse click]({% post_url 2025-12-19-mouse-click-from-atmega %})
- [scroll wheel]({% post_url 2025-12-29-scroll-wheel-on-atmega %})
- [motion sensor]({% post_url 2026-01-20-esp32c6-spi-pmw3320db-tydu-take-two %})

It seems like a good time to come up with a high level architecture design.
It could be argued that the code is small enough to put all in one Arduino
sketch, but I think it would be better to have some break out of the logical
components.

My thought is to have:
- `Button.cpp` 
- `ScrollWheel.cpp`
- `MotionSensor.cpp`
- `ex_g.ino` 

# Button.cpp

This will be a C++ class for handling the button logic. The constructor will
take a pin and a debounce time, in ms. There will be a public function to get
the current press or unpress state. The function will read the state of the pin
it was provided in its constructor and take into account the debounce time to
return the press or unpress state.

The idea is that there will be a `Button` instance representing each; left,
right, and middle buttons.

# ScrollWheel.cpp

This will be a C++ class for handling the scroll wheel motion. The constructor
will take the two pins to be read from. The class will provide a public function
to get the amount of scroll wheel movement since the last time it was called.
The function will return an indicator if there was scroll movement and if so, an
amount of scroll.

> I need to see if it works with Arduino, but I would like to use something like
[std::optional](https://en.cppreference.com/w/cpp/utility/optional.html) for the
return value, as opposed to a boolean sentinel.

# MotionSensor.cpp

This will be a C++ class for handling the motion sensor. The constructor will
take the four SPI pins and a desired DPI as input. The CIPO, COPI, and CLK SPI
pins will default to `-1`. This way they can be passed to the SPI library and
default to using the hardware specific SPI pins. The CS (chip select) will need
to be specified.

The DPI will be an unsigned integer that maps 1 to 1 to a desired DPI value,
i.e. 1500 would be 1500 DPI. The constructor will convert the
requested DPI to a valid multiple of 250 per the 
[PMW3320DB-TYDU]({% post_url 2025-12-31-pmw3320db-tydu-sensor %})
specification. The logic will also clamp the DPI between the minimum of 250 and
maximum of 3500.

The constructor will initialize the Arduino SPI library, using a 1 MHz clock
cycle. It will also preform the power on sequence for the PMW3320DB-TYDU via the
SPI interface using the Arduino SPI library.

A public function will be provided that will return the motion since the last
time the function was called. The function will leverage the streaming read of
the PMW3320DB-TYDU. The function will return an indicator for if there was
motion and if so, an amount of motion in the X and Y directions.

> Similar to the scroll wheel, I need to see if `std::optional` will work here.

# ex_g.ino

The project folder will be named `ex_g`, and per the 
[sketch build process](https://docs.arduino.cc/arduino-cli/sketch-build-process/),
the primary sketch file will need to be named `ex_g.ino` to match.

This file will define the standard `setup()` and `loop()` functions. 

The `setup()` will initialize the other components. Specifying which GPIO pins
are used for which behaviors. As well as specify any potential timing
constraints, i.e. debounce delay for the mouse buttons.

The `loop()` will poll each component for updated values and pass those on to
the Mouse library. The `loop()` will have no delays in it.

This file will be responsible for communicating with the Mouse library. Limiting
Mouse library communication to `ex_g.ino` serves a couple of purposes:

1. Having the `ex_g.ino` file talk with the Mouse library means that the library
could be switched out without changing the other components. For instance; if
left and right scroll support is needed, the standard Mouse library won't
work. Another library could be substituted restricting any changes to
`ex_g.ino`. However the other components would still function the same, simply
reading values from the GPIO pins.

2. The
[`Mouse.move()`](https://docs.arduino.cc/language-reference/en/functions/usb/Mouse/mouseMove/)
function takes the X and Y movement directions as well as the scroll directions.
If communicating with the Mouse library was in the individual components then
there would need to be two calls to `Mouse.move()`, or the motion sensor and
scroll wheel logic would need to be combined into the same component.

<div class="mermaid">
flowchart LR
    E[ex_g.ino] --> M[Mouse Library]
    W[ScrollWheel.cpp] --> E
    B[Button.cpp] --> E
    S[MotionSensor.cpp] --> E
</div>

# YAGNI

With the simplicity of actual code needed to implement the trackball logic one
could argue this design falls under
[YAGNI](https://en.wikipedia.org/wiki/You_aren't_gonna_need_it). 

The motion sensor module is named `MotionSensor.cpp`, and not after the
PMW3320DB-TYDU. One idea being that it could be replaced by another motion
sensor if a newer EX-G happens to update its hardware. This would allow the
`ex_g.ino` file to remain unchanged. Similar argument to the scroll wheel. The
file abstracts away that it's implemented as a rotary encoder.

It's likely that someone has written a fake implementation of the common Arduino
functions, `pinMode()`, `digitalRead()`, etc. This means I could potentially
test the components fairly easily by calling their common functions to get their
values since the last time they were called. 

Considering YAGNI brings up some questions:
- Am I going to write tests for this? Initially?
- What's the likelihood of me revisiting this to provide another mouse library?
- What's the likelihood of me re-using this code on a newer EX-G?
- Even if the previous two happen, is this componentization necessary right now?

I can't argue against the componentization and break up not being necessary at
this time. However, I feel that it's simple enough to do now. 

It's possible that I'm able to find pre-existing libraries that implement
the button and rotary encoder logic. So designing this way may make it easier to
integrate. It could also make it harder if I'm too rigid about how I think the
components should behave.

I think it's good to practice architecture design, even for small projects like
this one. Like many things it's a skill that needs practice in order to get
better. Practicing on something that is real, versus hypothetical, and that has
low risk should be taken advantage of.
