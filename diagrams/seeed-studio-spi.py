import schemdraw
import schemdraw.elements as elm
import schemdraw.pictorial as pictorial
from esp32 import Esp32c6Pictorial
from lonely_binary import LonelyBinary

with schemdraw.Drawing(show=False, file='../assets/esp32-spi.svg') as d:
    bb = pictorial.Breadboard().up().at(Esp32c6Pictorial.bb_offset())
    d += bb

    esp32 = Esp32c6Pictorial().at(bb.C1).anchor('D0')
    d += esp32
    lb = LonelyBinary().at(bb.F30).anchor('0_top')
    d += lb

    d += elm.Line().at(bb.J2).to(bb.R2_1).color('black')
    d += elm.Line().at(bb.R2_20).to(bb.J21).color('black')
    d += elm.Line().at(bb.I4).to(bb.I30).color('blue')
    d += elm.Line().at(bb.H6).to(bb.H29).color('brown')
    d += elm.Line().at(bb.B4).to(bb.B28).color('red')
