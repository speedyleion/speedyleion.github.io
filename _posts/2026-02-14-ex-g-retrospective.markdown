---
layout: post
title:  "EX-G Wired Trackball Retrospective"
date:   2026-02-14 14:00:03 -0800
categories: mice electronics arduino
---

This post is a look back on 
[Converting a Wireless Trackball to Wired]({% post_url 2025-12-14-wired-trackball %}).
I wanted to capture some thoughts while they're fresh in mind.

# Duration

I initially wrote down the high level plan on 2025-12-14. I'm writing this post
on 2026-02-14, exactly 2 months later. Like many people, I under estimated the
time it would take. I was thinking it might be done around the new year. I was
hoping to take advantage of the winter holidays to meet this new year deadline.
I had an overdue IOU to replace the floor in our laundry room. I underestimated
the flooring effort and it ate into the time I could spend on the trackball
during the winter holidays.

## Blogging

One of my goals was to blog about the effort. I am not a fast or efficient
writer. Most blog posts took 3-4 hours. I would be lucky if I got through the
writing effort in under 2 hours. Blogging about the journey likely doubled the
time cost of completing this task. 

The goal of blogging was to practice writing and communicating my thoughts. A
large part of writing is skill. Like any skill, it takes practice to get better.
I could benefit from taking a writing class or two, the act of writing is
something I can do on my own time and at my own pace. 

I tried a couple of approaches to the writing. Some posts were written after the
fact. These posts are usually written entirely in the past tense. 

Some posts I wrote as I did the work. I would write a plan for the next small
step, I would do the task, then I would write up results. Rinse and repeat. I'm
not sure how well they read to others, but I enjoyed writing those posts more.
It broke up the writing. More importantly, it helped me write out my thoughts
beforehand. Often my thoughts or hypothesis would be wrong. The past tense posts
would often have me omitting some of the mistakes I made to get to my result.

# What I Learned

I'm sure there's more, but these were ones I thought to write down as I went:

1. [Pull-(up/down) resistors]({% post_url 2025-12-19-mouse-click-from-atmega %}#adding-a-pull-down-resistor)
2. [Rotary Encoder]({% post_url 2025-12-29-scroll-wheel-on-atmega %}#rotary-encoder)
3. [Serial Peripheral Interface]({% post_url 2026-01-01-spi-and-pmw3320db-tydu %}#serial-peripheral-interface)
4. [Using a logic analyzer]({% post_url 2026-01-03-logic-analyzer-pmw3320db-tydu %})
5. [Schemdraw](https://schemdraw.readthedocs.io/en/stable/index.html)

The first topics are pretty well covered in their own posts. 

## Schemdraw

Schemdraw was a nice find. I really enjoy making programmatic diagrams. I often
use [mermaid.js](https://mermaid.js.org/) diagrams where I can. The programmatic
nature of the diagrams can feel a bit constraining at times, but it lends itself
to quick modifications and edits. They're also fairly concise for sharing.

I was able to leverage the:

- [analog circuits](https://schemdraw.readthedocs.io/en/stable/gallery/analog.html)
- [timing diagrams](https://schemdraw.readthedocs.io/en/stable/gallery/timing.html)
- [pictorial schematics](https://schemdraw.readthedocs.io/en/stable/gallery/pictorial.html)

I tried to use the pictorial schematics where I could. They provide a depiction
that's close to the real world, but are much cleaner than any picture I would
try to capture.

The source for all of the Schemdraw diagrams are available in the
[diagrams](https://github.com/speedyleion/speedyleion.github.io/tree/main/diagrams)
directory of this blog's GitHub repository.

# Giving Up

There were a number of times where I hit a roadblock that made me question if I
should cut my losses and end the activity.

1. After disassembly and realizing all components were attached directly to the
   circuit board.
2. After finding the 
[PMW-3320DB-TYDU data sheet](https://www.epsglobal.com/Media-Library/EPSGlobal/Products/files/pixart/PMW3320DB-TYDU.pdf?ext=.pdf)
and seeing that it lacked sufficient information for communicating with the
sensor.
3. After finding out the 
[Atmega32U4](https://www.amazon.com/Atmega32U4-Programming-Development-Micro-Controller-Compatible/dp/B0D83FBYPD)
was 5V and the PMW-3320DB-TYDU was 3V.
4. After discovering the ESP32C6 didn't support USB mouse

## Disassembly

I had mentioned in 
[Using EX-G hardware switches]({% post_url 2026-01-25-using-ex-g-hw-switches %}) how I
had hoped the switches used wiring so I could rewire easily. I also mentioned
in hindsight how this was a false hope. My limited experience with small
electronics seems to indicate that most of them put as many peripherals directly
on the circuit board as possible.

The feeling of giving up was fairly fleeting for this problem, but it was still
there.

## PMW-3320DB-TYDU

The optical sensor was a big unknown. I didn't do any research prior to the
tear down, so had no idea what I might be getting into. I was fortunate to run
across the 
[ADNS-3050 data sheet](https://media.digikey.com/pdf/data%20sheets/avago%20pdfs/adns-3050.pdf).
If I hadn't found the ADNS-3050 data sheet, I likely would have given up. Not
even trying to reverse engineer with a logic analyzer.

## 5V vs 3V

When I found out that the PMW-3320DB-TYDU couldn't handle more than 3.6V I must
have been in a bit of lull for the overall effort. It wasn't a major roadblock,
but it was enough that I was considering shelving the project.

For whatever reason I had latched onto using the Atmega32U4 and was looking for
a 3.3V version of it. They make 3.3V versions, they're just a bit harder to get
one's hands on. It took me a while to decide that I should try a different board
and chip. With the difficulty I had getting the
[ESP32S3](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/) into the
EX-G case, I think it's a good thing I didn't try to use the longer Atmega32U4
board.

## ESP32C6

I had chosen the 
[ESP32C6](https://www.seeedstudio.com/Seeed-Studio-XIAO-ESP32C6-p-5884.html) to
replace the Atmega32U4. 
When I found out the ESP32C6 didn't support mouse outputs over USB. I had to
look yet again for another solution. The ESP32C6 was already my second board to
try to complete this project with. I wasn't sure I wanted to keep trying more
boards. I had a better idea of what functionality to look for in a board, but it
was still pretty frustrating and made me consider ending the project.

I also considered trying to use the ESP32C6 as a bluetooth peripheral. I think
this would have greatly increased the scope of the project. I would have needed
to figure a way to power the board from the one AA battery the EX-G provides. I
also would have needed to figure out how to properly put the board to sleep and
wake-up based on the PMW3320DB-TYDU interrupt. This idea twirled around in my
head for a while before I finally decided it wasn't going to be a good path. If
I had tried down the bluetooth path, I've got a feeling the extra effort and
time likely would have resulted in me shelving the project before completion.

# The Failure Posts

There were two posts that were me failing to do what I had set out do.

- [Using Arduino UNO as logic analyzer]({% post_url 2026-01-02-arduino-logic-analyzer %})
- [Failing to Control the PMW3320DB-TYDU with SPI]({% post_url 2026-01-18-esp32c6-spi-pmw3320db-tydu %})

Often I end up communicating the good parts, or the final result. I have a habit
of not communicating failures until after I've gained some emotional distance
from them. Failing is a big part of learning. I struggle with embracing failures
for the benefit they give. These posts were a way to force myself to write
directly after I failed, or while I was failing. During the writing of the
posts it was tempting to not publish them. 

Giving the failures their own blog posts also helps to convey that failures
aren't always fast. Sometimes they take a while to realize them for what they
are. It's not uncommon that the work necessary for the correct solution only
takes the last 10% of the time, with the failures taking up the other 90% (those
are made up ratios).

I'm glad I took the time to write and publish those posts.

# Cost

I had to put in this section, because someone was giving me a hard time about
the cost of this project.

| description | cost |
| -- | -- |
| EX-G | $39.99 |
| Atmega32U4 (3pack) | $17.99 |
| logic analyzer | $19.99 |
| ESP32C6 (3pack) | $22.99 |
| ESP32S3 (3pack) | $26.99 |
| **total** | **$127.95** |

The table shows monetary cost. The time was quite a bit. Taking the low estimate
of 3 hours to write each post. I imagine the work the post was writing about was
likely close to 3 hours as well. There were 25 posts prior to this one. That
implies that it was at least 150 hours of effort. About 20 hours a week for 8
weeks.

# Summary

The biggest take away for me is **I finished the project**. 

It's very easy to take on a side project and get a little into it and then lose
interest. I was able to keep pushing through this project and come out on the
other side with a working solution. 

I also learned some new tools and insights along the way. It's nice to learn
things and be able to apply those learnings right away.

