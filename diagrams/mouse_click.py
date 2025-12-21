from tkinter import W
import schemdraw
import schemdraw.elements as elm
from schemdraw.elements.intcircuits import Ic, IcPin
import schemdraw.pictorial as pictorial

class Atmega(Ic):
    _element_defaults = {
        'edgepadW': 0.5,
        'edgepadH': 1,
        'pinspacing': 0.5,
        'leadlen': 0.5
    }
    def __init__(self, **kwargs):
        pins = [IcPin(name='9', side='left'),
                IcPin(name='8', side='left'),
                IcPin(name='7', side='left'),
                IcPin(name='6', side='left'),
                IcPin(name='5', side='left'),
                IcPin(name='4', side='left'),
                IcPin(name='3', side='left'),
                IcPin(name='2', side='left'),
                IcPin(name='GND', side='left', anchorname='GND1'),
                IcPin(name='GND', side='left', anchorname='GND2'),
                IcPin(name='RXI', side='left'),
                IcPin(name='TXO', side='left'),

                IcPin(name='10', side='right'),
                IcPin(name='16', side='right'),
                IcPin(name='14', side='right'),
                IcPin(name='15', side='right'),
                IcPin(name='A0', side='right'),
                IcPin(name='A1', side='right'),
                IcPin(name='A2', side='right'),
                IcPin(name='A3', side='right'),
                IcPin(name='VCC', side='right'),
                IcPin(name='RST', side='right'),
                IcPin(name='GND', side='right', anchorname='GND3'),
                IcPin(name='RAW', side='right')]
        super().__init__(pins=pins, botlabel='Atmega Board')

with schemdraw.Drawing(show=False, file='../assets/mouse_click_diagram.svg') as d:
    button = elm.Button().label('Push Button')
    d += button
    atmega = Atmega().at(button.end).anchor('9')
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
    atmega = Atmega().anchor('9')
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
    # The at(x, y) is a hack offset to prevent a bunch of empty space at the
    # left of the image
    bb = pictorial.Breadboard().up().at((-6.27, -2))
    d += bb

    # fritzing part from https://forum.fritzing.org/t/part-arduino-pro-micro-clone/10680
    atmega = pictorial.FritzingPart('pro_micro.fzpz').up().at(bb.D1).anchor('TXO')
    d += atmega

    d += elm.Line().at(bb.J4).to(bb.R1_3).color('red')
    d += elm.Line().at(bb.R1_15).to(bb.J16).color('red')

    button = pictorial.FritzingPart('push_button.fzpz').at(bb.E16).anchor('Pin 4')
    d += button
    
    d += elm.Line().at(bb.B16).to(bb.B12).color('blue')

with schemdraw.Drawing(show=False, file='../assets/mouse_click_pull_down_bb.svg') as d:
    # The at(x, y) is a hack offset to prevent a bunch of empty space at the
    # left of the image
    bb = pictorial.Breadboard().up().at((-6.27, -2))
    d += bb

    # fritzing part from https://forum.fritzing.org/t/part-arduino-pro-micro-clone/10680
    atmega = pictorial.FritzingPart('pro_micro.fzpz').up().at(bb.D1).anchor('TXO')
    d += atmega

    d += elm.Line().at(bb.J4).to(bb.R1_3).color('red')
    d += elm.Line().at(bb.R1_15).to(bb.J16).color('red')

    button = pictorial.FritzingPart('push_button.fzpz').at(bb.E16).anchor('Pin 4')
    d += button
    
    d += elm.Line().at(bb.B16).to(bb.B12).color('blue')
    pictorial.Resistor(10000).at(bb.A4).to(bb.A12)

with schemdraw.Drawing(show=False, file='../assets/mouse_click_pull_down_bb_working.svg') as d:
    # The at(x, y) is a hack offset to prevent a bunch of empty space at the
    # left of the image
    bb = pictorial.Breadboard().up().at((-6.27, -2))
    d += bb

    # fritzing part from https://forum.fritzing.org/t/part-arduino-pro-micro-clone/10680
    atmega = pictorial.FritzingPart('pro_micro.fzpz').up().at(bb.D1).anchor('TXO')
    d += atmega

    d += elm.Line().at(bb.J4).to(bb.R1_3).color('red')
    d += elm.Line().at(bb.R1_15).to(bb.J16).color('red')

    button = pictorial.FritzingPart('push_button.fzpz').at(bb.E16).anchor('Pin 4')
    d += button
    
    d += elm.Line().at(bb.B18).to(bb.B12).color('blue')
    pictorial.Resistor(10000).at(bb.A4).to(bb.A12)
