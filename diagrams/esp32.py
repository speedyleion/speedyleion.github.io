from schemdraw.elements.intcircuits import Ic, IcPin
import schemdraw.pictorial as pictorial

class Esp32c6Ic(Ic):
    """
    An ESP32-C6 IC representation to be used in circuit diagrams.
    """
    def __init__(self, **kwargs):
        pins = [IcPin(name='D6', side='left'),
                IcPin(name='D5', side='left'),
                IcPin(name='D4', side='left'),
                IcPin(name='D3', side='left'),
                IcPin(name='D2', side='left'),
                IcPin(name='D1', side='left'),
                IcPin(name='D0', side='left'),

                IcPin(name='D7', side='right'),
                IcPin(name='D8', side='right'),
                IcPin(name='D9', side='right'),
                IcPin(name='D10', side='right'),
                IcPin(name='3.3V', side='right'),
                IcPin(name='GND', side='right'),
                IcPin(name='5V', side='right')]
        super().__init__(pins=pins, botlabel='ESP32C6')

class Esp32c6Pictorial(pictorial.FritzingPart):
    """
    Fritzing part for the esp32c6 from
    https://github.com/Seeed-Studio/fritzing_parts/blob/master/XIAO%20Boards/Seeed%20Studio%20XIAO%20ESP32C6.fzpz
    """
    def __init__(self, **kwargs):
        super().__init__('seeed-studio-xiao-esp32c6.fzpz', **kwargs)
    
    @classmethod
    def bb_offset(cls):
        """
        # The at(x, y) is a hack offset to prevent a bunch of empty space at the
        # left of the image
        """
        # return (-6.27, -2)
        return (0, 0)