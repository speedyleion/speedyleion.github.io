import schemdraw
import schemdraw.elements as elm
import schemdraw.pictorial as pictorial
from atmega import AtmegaIc, AtmegaPictorial

with schemdraw.Drawing(show=False, file='../assets/internal_pull_up.svg') as d:
    button = elm.Button().label('Push Button')
    d += button
    atmega = AtmegaIc().at(button.end).anchor('GND1')
    d += atmega
    d += elm.lines.Wire('-|').to(button.start).at(getattr(atmega, '9'))

with schemdraw.Drawing(show=False, file='../assets/internal_pull_up_bb.svg') as d:
    bb = pictorial.Breadboard().up().at(AtmegaPictorial.bb_offset())
    d += bb

    atmega = AtmegaPictorial().up().at(bb.D1).anchor('TXO')
    d += atmega

    d += elm.Line().at(bb.L2_3).to(bb.A4).color('black')
    d += elm.Line().at(bb.L2_17).to(bb.A18).color('black')
    d += elm.Line().at(bb.B12).to(bb.B16).color('black')

    button = pictorial.FritzingPart('push_button.fzpz').at(bb.E16).anchor('Pin 4')
    d += button