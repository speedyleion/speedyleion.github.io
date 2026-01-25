
import schemdraw
import schemdraw.elements as elm
import schemdraw.pictorial as pictorial
from esp32 import Esp32c6Pictorial
from schemdraw.util import Point


with schemdraw.Drawing(show=False, file='../assets/ex_g_on_board_switch.svg') as d:
    bb = pictorial.Breadboard().up()
    d += bb

    esp32 = Esp32c6Pictorial().at(bb.C1).anchor('D0')
    d += esp32

    button = pictorial.FritzingPart('push_button.fzpz').at(bb.L1_4 + Point((0, -1))).anchor('Pin 3')
    d += button

    d += elm.Wire('|-').at(bb.A5).to(button.absanchors['Pin 3']).color('blue')
    gnd = elm.Line().at(button.absanchors['Pin 2']).down().length(0.75).color('black')
    d += gnd
    d += elm.Ground().at(gnd.end)
    d += elm.Line().at(bb.I2).right().to(bb.I10).color('black')
    d += elm.Line().down().toy(gnd.end).color('black')
    d += elm.Ground()