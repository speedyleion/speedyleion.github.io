from schemdraw.elements.intcircuits import Ic, IcPin
import schemdraw.pictorial as pictorial

class AtmegaIc(Ic):
    """
    An Atmega IC representation to be used in circuit diagrams.
    """
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

class AtmegaPictorial(pictorial.FritzingPart):
    """
    Fritzing part for the Atmega on a pro micro board from https://forum.fritzing.org/t/part-arduino-pro-micro-clone/10680
    """
    def __init__(self, **kwargs):
        super().__init__('pro_micro.fzpz', **kwargs)
    
    @classmethod
    def bb_offset(cls):
        """
    # The at(x, y) is a hack offset to prevent a bunch of empty space at the
    # left of the image
        """
        return (-6.27, -2)