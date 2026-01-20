---
layout: post
title:  "Using Arduino UNO as logic analyzer"
date:   2026-01-02 18:00:03 -0800
categories: mice electronics arduino
---

Building on my investigation in the previous 
[post]({% post_url 2026-01-01-spi-and-pmw3320db-tydu %}), I wanted to be able to
see what messages the [EX-G][ex-g] trackball controller was sending to the
PMW3320DB-TYDU mouse sensor. I was pretty sure a 
[logic analyzer](https://en.wikipedia.org/wiki/Logic_analyzer) would allow me to
investigate the communication. Not having a dedicated logic analyzer, I
attempted to use the Arduino UNO that I had available as a logic analyzer.

# Logic Analyzer libraries

I found two possibilities for using the Arduino as a logic analyzer:

1. A logic analyzer library on Github,
[https://github.com/pschatzmann/logic-analyzer](https://github.com/pschatzmann/logic-analyzer)
2. The [LogicAnalyzer](https://docs.arduino.cc/libraries/logicanalyzer/) library
available via the [Arduino Library Reference](https://docs.arduino.cc/libraries/)

I wanted to go with the library I found on Github, because it mentioned trying
to improve on Arduino LogicAnalyzer library and its
[example](https://github.com/pschatzmann/logic-analyzer?tab=readme-ov-file#the-basic-arduino-sketch)
looked pretty easy to use. However, reading further through the
[documentation](https://github.com/pschatzmann/logic-analyzer?tab=readme-ov-file#supported-boards)
I saw that for AVR processors it only supported 110Khz and 500 samples. With the
PMW3320DB-TYDU supporting up to 1Mhz the 110Khz didn't seem like it would have
the resolution necessary to capture the messages. 500 samples is also a very
small window to try and get the events to happen and then record them. If I did
the math correctly it would only have a ~4ms window. With all that in mind I
chose to go with the Arduino LogicAnalyzer library.

The Arduino LogicAnalyzer library provides an example sketch,
[logic_analyzer_sigrok.ino](https://github.com/gillham/logic_analyzer/blob/master/examples/logic_analyzer_sigrok/logic_analyzer_sigrok.ino),
that works with the [PulseView](https://sigrok.org/wiki/Downloads) GUI tool. To
be honest, that _example_ sketch seemed pretty complex compared to the example
from
[https://github.com/pschatzmann/logic-analyzer](https://github.com/pschatzmann/logic-analyzer).
I figured I would try it out and see what happens. It compiled and uploaded to
the Arduino UNO with no problem.

# PulseView

In order to visualize the data, I would need some kind of GUI. A common one that
people seem to use is 
[PulseView](https://sigrok.org/wiki/Downloads).

The download page has a heading:

> Nightly builds (recommended, always up-to-date)

I downloaded the nightly version for Mac and attempted to run it. It didn't open
any graphical window. I had to go into Activity Monitor and force kill it.

I decided to grab the most recent release, 0.4.2, for Mac. I was curious when
this version was released, so did some digging through their repo.
[pulsview-0.4.2](https://sigrok.org/gitweb/?p=pulseview.git;a=commit;h=2b526a42a2fd68d513d4c2061790605a0c7add6c)
appears to have been released in March of 2020. While this is almost 6 years
ago, logic analyzers have been around for a while so it could be that it doesn't
need many changes. At the same time, Mac OS has changed a bit since then i.e.
the Intel to Arm transition, so fingers crossed. 

This version did run. It got initially blocked by
[GateKeeper](https://en.wikipedia.org/wiki/Gatekeeper_(macOS)), but it's older
software and open source isn't convenient to get Apple code signing, so I went
into the security settings and allowed PulseView to run.

## Connecting PulseView to the Arduino

For connecting PulseView to the Arduino I followed a slightly modified version
of the
[steps](https://github.com/pschatzmann/logic-analyzer?tab=readme-ov-file#connecting-to-pulseview)
in the logic analyzer library that I didn't use:

- Select "Connect to a Device":
    - Choose the Driver: Openbentch Logic Sniffer & SUMP Compatibles
    - Choose the Interface: 
        - Serial Port 
        - Port that the Arduino Uno shows up on
        - Choose 115200 baud, to align with the `Serial.begin(115200)` from the
        [logic_analyzer_sigrok.ino](https://github.com/gillham/logic_analyzer/blob/6ec9441ad6052d5326de4ecf1db61404bd5c32bf/examples/logic_analyzer_sigrok/logic_analyzer_sigrok.ino#L215)
    - Click on "Scan for Devices using driver above" button
    - Select the Device - "AGLAv0 with 6 channels"

These steps need to be performed with the Arduino Uno flashed with the logic
analyzer sketch and currently plugged into the computer.

# Using the Logic Analyzer

During the [disassembly]({% post_url 2025-12-26-disassemble-ex-g %}) of the EX-G
trackball I noted some points at the underside of where the PMW3320DB-TYDU
ribbon attaches to the circuit board:

![EX-G PCB1 underneath trackball sensor ribbon cable](/assets/ex-g-pcb1-under-ribbon.png)

I previously didn't know what some of the points were for. After 
[learning about SPI]({% post_url 2026-01-01-spi-and-pmw3320db-tydu %}), I can
say what these points likely represent

- SD: The SPI data line
- NCS: SPI chip select. It seems `N` means "not chip select" indicating that
when this line goes low the chip is selected.
- SC: The SPI clock line

The logic analyzer sketch uses Arduino pins 8-13. I was sure I couldn't couldn't
attach pin 8 to `SD` and things would work. The logic analyzer needed some kind
of reference to know when `SD` is low or high. I wasn't sure if I should attach
pin 9 to the ground on the EX-G circuit board. Looking in the logic analyzer
sketch there didn't seem to be good instructions on how to actually use it. 

After doing some internet searching for a bit, I ran across
[http://www.microtan.ukpc.net/Tools/LA_Linux.html](http://www.microtan.ukpc.net/Tools/LA_Linux.html).
Under the heading "Using Logic Sniffer" it had this instruction:

> Connect ground wire from Arduino pin GND to equipment ground.

With a battery powering the EX-G and all of its electrical components connected
back up. I connected the Arduino `GND` to the `GND` on the EX-G circuit board. I
then connected pin 8 from the Arduino to the `SD` point on the EX-G circuit
board. I then clicked on the "Run" button in PulseView. The run lasted a few
seconds and stopped. It showed a solid low line for channel 0. For my next test
I started continually moving the trackball, with everything still connected, and
hit the "Run" button. Still a solid low line for channel 0. I retried the
previous tests using Pin 9, which is channel 1 in PulseView, still solid low
line.

I realized the Arduino is a 5V system meaning it's looking for a 5V high line.
While the PMW3320DB-TYDU is in a ?V system. At this point I realized I didn't
know what it was operating at as part of the EX-G. From the 
[data sheet](https://www.epsglobal.com/Media-Library/EPSGlobal/Products/files/pixart/PMW3320DB-TYDU.pdf?ext=.pdf)
the operating range is 2.1V to 3.4V. I grabbed my multimeter and checked between
`GND` and `NCS`, giving me 2.2V. I chose `NCS` since it is high until the chip
was selected, so as long as I didn't touch the trackball it should be high while
measuring. Doing some digging online, Arduino's don't register a digital high
until ~3V. This means the 2.2V is too low to register for the Arduino. 

This means I would need a level shifter (some thing I recently learned about) to
get the Arduino to see the change.  Web searches for "arduino uno level shifter
from 2.2v to 5v" kept coming back suggesting getting a dedicated level shifter
board. It was getting late, so I decided to punt it over to the AI overlords. AI
suggested using a circuit with a transistor to step up the voltage. I asked AI
if the transistor could handle 1Mhz transitions and it assured me it could.
Whether this is true, I don't really know.

![Image of step up level shifter using transistor](/assets/level_shifter.svg)

Wiring this up to the Arduino looked something like:

![Pictorial of step up level shifter with Arduino](/assets/level_shifter_bb.svg)

[Arduino Image Source](https://commons.wikimedia.org/wiki/File:ArduinoUNO.png), CC-BY-SA-3.0.

> After wiring this up, I did run across
[https://docs.arduino.cc/learn/microcontrollers/5v-3v3/#stepping-up](https://docs.arduino.cc/learn/microcontrollers/5v-3v3/#stepping-up)
which covers a similar approach to a level shifter.

Retrying the previous steps where I connected SDIO from the bread board to the
EX-G `SD` point, I now was getting a solid logical low when not touching the
trackball. If I manipulated the trackball when pressing the "Run" button, I
could see the line go high, but it was a solid high line, no jumps or cycling of
the line to indicate low and high data bits.

Due to:
- having to go through the level up shifter
- physical difficulty trying to simultaneously 
    - manipulate the trackball
    - hold the wires on the correct terminals of the EX-G circuit board
    - click the "Run" button in PulseView
- short capture length of PulseView
- only getting constant logic low or logic high

I decided to chalk the Arduino logic analyzer up as a failure and pivot. Looking
to see what inexpensive logic analyzers were out there. I decided to order the 
[Lonely Binary Logic Analyzer](https://lonelybinary.com/en-us/products/dla?_pos=1&_sid=2e6665640&_ss=r). 
This one was chosen as it was inexpensive and 
[it works](https://lonelybinary.com/en-us/blogs/logic-analyzer-quickstart-1/03-logic-2) 
with [Saleae Logic Pro 2](https://saleae.com/downloads).

It may have been the limitations of the Arduino as a logic analyzer, but I
wasn't very impressed with using PulseView and want to be able to try something
else. Since Saleae sells some more expensive logic analyzers,
[https://saleae.com/logic](https://saleae.com/logic), I'm hoping their GUI is a
better experience.

Next: get the Lonely Binary logic analyzer and re-attempt capturing SPI
data between the EX-G and sensor.

# PS

I did not capture screenshots of using PulseView or more detailed info of how I
used it since it didn't work out for me. While I can understand that having the
details could help someone potentially find out where I may have gone wrong if
the tools really could work for my use case, I didn't want to sink too much time
into a path that wasn't getting me anywhere.

[ex-g]: https://elecomusa.com/products/ex-g-trackball-wireless-usb-copy
