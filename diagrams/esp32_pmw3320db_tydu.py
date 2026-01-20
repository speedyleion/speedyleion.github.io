import schemdraw
import schemdraw.elements as elm
from esp32 import Esp32c6Ic, Esp32c6Pictorial
from pmw3320db_tydu import PMW3320DB
import schemdraw.pictorial as pictorial
from schemdraw.util import Point

with schemdraw.Drawing(show=False, file='../assets/esp32-pmw3320db-tydu.svg') as d:
    esp32 = Esp32c6Ic()
    d += esp32
    d += elm.lines.Line().at(esp32.GND).right().length(4)
    pmw3320db = PMW3320DB().anchor('GND')
    d += pmw3320db
    d += elm.lines.Wire('-|').at(getattr(esp32, '3.3V')).to(pmw3320db.VDD)
    r = elm.Resistor().right().label('1kΩ', loc='top', ofst=-0.05).at(esp32.D10)
    d += elm.lines.Line().at(r.end).toy(esp32.D9).dot()
    d += elm.lines.Wire('-|').at(esp32.D9).to(pmw3320db.SDIO)
    d += elm.lines.Line().at(esp32.D8).right().length(0.5)
    d += elm.lines.Wire('|-').to(pmw3320db.SCLK)
    d += elm.lines.Line().at(esp32.D3).left().length(0.25)
    d += elm.lines.Line().up().length(3)
    d += elm.lines.Wire('-|').to(pmw3320db.NCS)

with schemdraw.Drawing(show=False, file='../assets/esp32-pmw3320db-tydu-interrupt.svg') as d:
    esp32 = Esp32c6Ic()
    d += esp32
    d += elm.lines.Line().at(esp32.GND).right().length(4)
    pmw3320db = PMW3320DB().anchor('GND')
    d += pmw3320db
    d += elm.lines.Wire('-|').at(getattr(esp32, '3.3V')).to(pmw3320db.VDD)
    r = elm.Resistor().right().label('1kΩ', loc='top', ofst=-0.05).at(esp32.D10)
    d += elm.lines.Line().at(r.end).toy(esp32.D9).dot()
    d += elm.lines.Wire('-|').at(esp32.D9).to(pmw3320db.SDIO)
    d += elm.lines.Line().at(esp32.D8).right().length(0.5)
    d += elm.lines.Wire('|-').to(pmw3320db.SCLK)
    d += elm.lines.Line().at(esp32.D3).left().length(0.25)
    d += elm.lines.Line().up().length(3)
    d += elm.lines.Wire('-|').to(pmw3320db.NCS)
    d += elm.lines.Line().at(esp32.D4).left().length(0.75)
    d += elm.lines.Line().up().length(4.3)
    d += elm.lines.Wire('c', k=13).to(pmw3320db.MOTION)

with schemdraw.Drawing(show=False, file='../assets/esp32-pmw3320db-tydu-bb.svg') as d:
    pmw3320db = pictorial.FritzingPart('dip_8_pin.fzpz')
    d += pmw3320db
    bb = pictorial.Breadboard().up().at(pmw3320db.pin1 + Point((0, -2))).anchor('R2_1')
    d += bb

    esp32 = Esp32c6Pictorial().at(bb.C1).anchor('D0')
    d += esp32

    h3 = bb.H3
    h5 = bb.H5
    lift = 0.25
    offset = 0.1
    resistor_1k = pictorial.Resistor(1000).at((h3[0] + offset, h3[1] + lift)).tox(bb.H5)
    d += elm.Line().at(bb.H4).to(resistor_1k.start).color('grey')
    d += elm.Line().at(h5).to(resistor_1k.end).color('grey')
    d += resistor_1k.label('1kΩ', loc='top', ofst=Point((-0.9,-0.35)))

    d += elm.Wire('n', k=2.3).at(bb.J2).to(pmw3320db.pin2)
    d += elm.Wire('n', k=2).at(bb.J3).to(pmw3320db.pin3).color('red')
    d += elm.Line().at(bb.J5).up().length(2).color('blue')
    d += elm.Line().right().length(0.75).color('blue')
    d += elm.Wire('n', k=2.5).to(pmw3320db.pin5).color('blue')
    d += elm.Wire('n', k=2.6).at(bb.J6).to(pmw3320db.pin1).color('brown')
    d += elm.Line().at(bb.B4).left().length(1.75).color('green')
    d += elm.Wire('n', k=8).to(pmw3320db.pin8).color('green')

with schemdraw.Drawing(show=False, file='../assets/esp32-pmw3320db-tydu-bb-interrupt.svg') as d:
    pmw3320db = pictorial.FritzingPart('dip_8_pin.fzpz')
    d += pmw3320db
    bb = pictorial.Breadboard().up().at(pmw3320db.pin1 + Point((0, -2))).anchor('R2_1')
    d += bb

    esp32 = Esp32c6Pictorial().at(bb.C1).anchor('D0')
    d += esp32

    h3 = bb.H3
    h5 = bb.H5
    lift = 0.25
    offset = 0.1
    resistor_1k = pictorial.Resistor(1000).at((h3[0] + offset, h3[1] + lift)).tox(bb.H5)
    d += elm.Line().at(bb.H4).to(resistor_1k.start).color('grey')
    d += elm.Line().at(h5).to(resistor_1k.end).color('grey')
    d += resistor_1k.label('1kΩ', loc='top', ofst=Point((-0.9,-0.35)))

    d += elm.Wire('n', k=2.3).at(bb.J2).to(pmw3320db.pin2)
    d += elm.Wire('n', k=2).at(bb.J3).to(pmw3320db.pin3).color('red')
    d += elm.Line().at(bb.J5).up().length(2).color('blue')
    d += elm.Line().right().length(0.75).color('blue')
    d += elm.Wire('n', k=2.5).to(pmw3320db.pin5).color('blue')
    d += elm.Wire('n', k=2.6).at(bb.J6).to(pmw3320db.pin1).color('brown')
    d += elm.Line().at(bb.B4).left().length(1.75).color('green')
    d += elm.Wire('n', k=8).to(pmw3320db.pin8).color('green')
    d += elm.Line().at(bb.A5).left().length(2.4).color('pink')
    d += elm.Wire('n', k=8.65).to(pmw3320db.pin7).color('pink')