import schemdraw
import schemdraw.elements as elm
import schemdraw.pictorial as pictorial
from atmega import AtmegaIc, AtmegaPictorial

with schemdraw.Drawing(show=False, file='../assets/mouse_click_diagram.svg') as d:
    button = elm.Button().label('Push Button')
    d += button
    atmega = AtmegaIc().at(button.end).anchor('9')
    d += atmega
    bbox = atmega.get_bbox(transform=True)
    height = bbox.ymax - bbox.ymin
    width = bbox.xmax - bbox.xmin
    d += elm.Line().right(d.unit * 0.5).at(atmega.VCC)
    d += elm.Line().down(height * 0.75)
    d += elm.Line().left().tox(button.start)
    d += elm.Line().up().toy(button.start)

with schemdraw.Drawing(show=False, file='../assets/mouse_click_pull_down_diagram.svg') as d:
    button = elm.Button().label('Push Button')
    d += button
    d += elm.Line().right(d.unit * 0.5)
    atmega = AtmegaIc().anchor('9')
    d += atmega
    bbox = atmega.get_bbox(transform=True)
    height = bbox.ymax - bbox.ymin
    width = bbox.xmax - bbox.xmin
    d += elm.Line().right(d.unit * 0.5).at(atmega.VCC)
    d += elm.Line().down(height * 0.75)
    d += elm.Line().left().tox(button.start)
    d += elm.Line().up().toy(button.start)
    d +=elm.Resistor().up().at(button.end).label(r'$10K\Omega$')
    d += elm.Line().up().toy(atmega.GND1)
    d += elm.Line().right().to(atmega.GND1)

with schemdraw.Drawing(show=False, file='../assets/mouse_click_bb.svg') as d:
    bb = pictorial.Breadboard().up().at(AtmegaPictorial.bb_offset())
    d += bb

    atmega = AtmegaPictorial().up().at(bb.D1).anchor('TXO')
    d += atmega

    d += elm.Line().at(bb.J4).to(bb.R1_3).color('red')
    d += elm.Line().at(bb.R1_15).to(bb.J16).color('red')

    button = pictorial.FritzingPart('push_button.fzpz').at(bb.E16).anchor('Pin 4')
    d += button
    
    d += elm.Line().at(bb.B16).to(bb.B12).color('blue')

with schemdraw.Drawing(show=False, file='../assets/mouse_click_pull_down_bb.svg') as d:
    bb = pictorial.Breadboard().up().at(AtmegaPictorial.bb_offset())
    d += bb

    atmega = AtmegaPictorial().up().at(bb.D1).anchor('TXO')
    d += atmega

    d += elm.Line().at(bb.J4).to(bb.R1_3).color('red')
    d += elm.Line().at(bb.R1_15).to(bb.J16).color('red')

    button = pictorial.FritzingPart('push_button.fzpz').at(bb.E16).anchor('Pin 4')
    d += button
    
    d += elm.Line().at(bb.B16).to(bb.B12).color('blue')
    pictorial.Resistor(10000).at(bb.A4).to(bb.A12)

with schemdraw.Drawing(show=False, file='../assets/mouse_click_pull_down_bb_working.svg') as d:
    bb = pictorial.Breadboard().up().at(AtmegaPictorial.bb_offset())
    d += bb

    atmega = AtmegaPictorial().up().at(bb.D1).anchor('TXO')
    d += atmega

    d += elm.Line().at(bb.J4).to(bb.R1_3).color('red')
    d += elm.Line().at(bb.R1_15).to(bb.J16).color('red')

    button = pictorial.FritzingPart('push_button.fzpz').at(bb.E16).anchor('Pin 4')
    d += button
    
    d += elm.Line().at(bb.B18).to(bb.B12).color('blue')
    pictorial.Resistor(10000).at(bb.A4).to(bb.A12)
