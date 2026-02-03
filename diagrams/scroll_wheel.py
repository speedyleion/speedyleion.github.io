import schemdraw
import schemdraw.elements as elm
import schemdraw.pictorial as pictorial
from schemdraw.elements.intcircuits import Ic, IcPin
from schemdraw.util import Point
from atmega import AtmegaIc, AtmegaPictorial
import schemdraw.logic as logic
from esp32 import Esp32c6Pictorial

class WheelEncoder(Ic):
    """
    A scroll wheel rotary encoder.
    """
    _element_defaults = {
        'edgepadW': 0.5,
        'edgepadH': 1,
        'pinspacing': 0.5,
        'leadlen': 0.5
    }
    def __init__(self, **kwargs):
        pins=[
            IcPin(name='CLK', side='right'),
            IcPin(name='DT', side='right'),
            IcPin(name='COM', side='right'),
        ]
        super().__init__(pins=pins, botlabel='Scroll Wheel')

with schemdraw.Drawing(show=False, file='../assets/scroll_wheel.svg') as d:
    enc = WheelEncoder()
    d += enc
    line = elm.Line().right().at(enc.COM)
    d += line

    atmega = AtmegaIc().at(line.end).anchor('GND1')
    d += atmega

    d += elm.lines.Wire('-|').at(enc.CLK).to(getattr(atmega, '3'))
    d += elm.lines.Wire('-|').at(enc.DT).to(getattr(atmega, '2'))

with schemdraw.Drawing(show=False, file='../assets/scroll_wheel_bb.svg') as d:
    bb = pictorial.Breadboard().up().at(AtmegaPictorial.bb_offset())
    d += bb

    atmega = AtmegaPictorial().up().at(bb.D1).anchor('TXO')
    d += atmega


    enc = pictorial.FritzingPart('rotary_encoder.fzpz').left().at(bb.A5 + Point((0, -3))).anchor('EncoderPinC')
    d += enc

    d += elm.Line().at(enc.EncoderPinB).to(bb.A4).color('black')
    d += elm.Line().at(enc.EncoderPinC).to(bb.A5).color('black')
    d += elm.Line().at(enc.EncoderPinA).to(bb.A6).color('black')

    # Hack bbox expansion to keep the encoder visible
    d += elm.Line().at(bb.A5 + Point((0, -5))).to(bb.A5 + Point((0, -5))).color(None)

with schemdraw.Drawing(show=False, file='../assets/rotary_encoder_signal.svg') as d:
    logic.TimingDiagram({
        'signal': [
            {'name': 'a', 'wave': '0.1.0.1.'},  
            {'name': 'b', 'wave': '01.0.1.0'},  
            ],
        'edge': ['[0^:0.5]-[0^:0.5]{none,:} 0,0',
            '[0^:1.5]-[0^:1.5]{none,:} 0,1',
            '[0^:2.5]-[0^:2.5]{none,:} 1,1',
            '[0^:3.5]-[0^:3.5]{none,:} 1,0'

         ]}, risetime=0, grid=False)

with schemdraw.Drawing(show=False, file='../assets/scroll_wheel_esp32_bb.svg') as d:
    bb = pictorial.Breadboard().up()
    d += bb
    esp32 = Esp32c6Pictorial().at(bb.C2).anchor('D1')
    d += esp32

    enc = pictorial.FritzingPart('rotary_encoder.fzpz').left().at(bb.A2 + Point((0, -3))).anchor('EncoderPinC')
    d += enc

    d += elm.Line().at(enc.EncoderPinB).to(bb.A1).color('lightgrey')
    d += elm.Line().at(enc.EncoderPinC).to(bb.A2).color('lightgrey')
    lead = elm.Line().at(enc.EncoderPinA).up(2.5).color('black')
    d += lead
    d += elm.Wire('c', 3).at(bb.H2).to(lead.end).color('black')
    # d += elm.Line().at(enc.EncoderPinA).to(bb.A3).color('black')

    # Hack bbox expansion to keep the encoder visible
    d += elm.Line().at(bb.A5 + Point((0, -5))).to(bb.A5 + Point((0, -5))).color(None)

with schemdraw.Drawing(show=False, file='../assets/scroll_wheel_esp32_wired_correct_bb.svg') as d:
    bb = pictorial.Breadboard().up()
    d += bb
    esp32 = Esp32c6Pictorial().at(bb.C2).anchor('D1')
    d += esp32

    enc = pictorial.FritzingPart('rotary_encoder.fzpz').left().at(bb.A1 + Point((0, -3))).anchor('EncoderPinC')
    d += enc

    lead = elm.Line().at(enc.EncoderPinB).up(2.5).color('lightgrey')
    d += lead
    d += elm.Line().at(enc.EncoderPinC).to(bb.A1).color('lightgrey')
    d += elm.Line().at(enc.EncoderPinA).to(bb.A2).color('black')
    d += elm.Wire('c', -1).at(bb.H2).to(lead.end).color('lightgrey')
    # d += elm.Line().at(enc.EncoderPinA).to(bb.A3).color('black')

    # Hack bbox expansion to keep the encoder visible
    d += elm.Line().at(bb.A5 + Point((0, -5))).to(bb.A5 + Point((0, -5))).color(None)


with schemdraw.Drawing(show=False, file='../assets/rotary_encoder_bad_ground_signal.svg') as d:
    logic.TimingDiagram({
        'signal': [
            {'name': 'a', 'wave': '0.1.0.1.'},  
            {'name': 'b', 'wave': '01..01..'},  
            ],
        'edge': ['[0^:0.5]-[0^:0.5]{none,:} 0,0',
            '[0^:1.5]-[0^:1.5]{none,:} 0,1',
            '[0^:2.5]-[0^:2.5]{none,:} 1,1',
            '[0^:3.5]-[0^:3.5]{none,:} 1,1'

         ]}, risetime=0, grid=False)