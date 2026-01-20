
import schemdraw 
from schemdraw.elements.intcircuits import Ic, IcPin
class PMW3320DB(Ic):
    """
    An PMW3320DB IC representation to be used in circuit diagrams.
    """
    def __init__(self, **kwargs):

        pins = [IcPin(name='REG', side='left', pin="8"),
                IcPin(name='VDD', side='left', pin="7"),
                IcPin(name='GND', side='left', pin="6"),
                IcPin(name='SCLK', side='left', pin="5"),

                IcPin(name='SDIO', side='right', pin="1"),
                IcPin(name='LED', side='right', pin="2"),
                IcPin(name='MOTION', side='right', pin="3"),
                IcPin(name='NCS', side='right', pin="4")]
        super().__init__(pins=pins, botlabel='PMW3320DB-TYDU')

if __name__ == '__main__':
    with schemdraw.Drawing(show=False, file='../assets/pmw3320db-tydu.svg') as d:
        pmw = PMW3320DB()
        d += pmw