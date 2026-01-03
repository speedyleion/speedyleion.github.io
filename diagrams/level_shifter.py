import schemdraw
import schemdraw.elements as elm
from schemdraw.elements.intcircuits import Ic, IcPin
import schemdraw.pictorial as pictorial

with schemdraw.Drawing(show=False, file='../assets/level_shifter.svg') as d:
    sensor = Ic(
        pins = [
            IcPin(name='GND', side='right'),
            IcPin(name='SDIO', side='right'),
        ],
        botlabel='Sensor (2.2V)'
    )
    d += sensor

    d += elm.Line().at(sensor.GND).down(d.unit * 0.3)
    gnd1 = elm.Ground()
    d += gnd1
    
    
    r_base = elm.Resistor().right().label('1kΩ').at(sensor.SDIO)
    d += r_base
    
    bjt = elm.BjtNpn().right().anchor('base')
    d += bjt.label('BC547B')
    
    d += elm.Line().at(bjt.emitter).down().toy(gnd1.start.y)
    d += elm.Ground()
    
    
    d += elm.Line().at(bjt.collector).right()
    arduino = Ic(
        pins = [
            IcPin(name='GND', side='left'),
            IcPin(name='Pin 8', side='left'),
            IcPin(name='5V', side='left'),
        ],
        botlabel='Arduino Uno'
    ).anchor('Pin 8')
    d += arduino
    
    d += elm.Line().at(arduino.GND).down().toy(gnd1.start.y)
    d += elm.Ground()

    r_pullup = elm.Resistor().left().label('4.7kΩ').at(getattr(arduino, '5V'))
    d += r_pullup
    d += elm.lines.Wire('-|').at(r_pullup.end).to(bjt.collector)

# Copied from https://schemdraw.readthedocs.io/en/stable/elements/pictorial.html#example
class ArduinoUno(elm.ElementImage):
    ''' Arduino Element '''
    def __init__(self):
        width = 10.3  # Set the width to scale properly for 0.1 inch pin spacing on headers
        height = width/1.397  # Based on image dimensions
        super().__init__('arduino_uno.png', width=width, height=height, xy=(-.75, 0))
        # Define all the anchors
        top = height * .956
        arefx = 3.4
        pinspace = pictorial.PINSPACING
        for i, pinname in enumerate(['aref', 'gnd_top', 'pin13', 'pin12', 'pin11',
                                    'pin10', 'pin9', 'pin8']):
            self.anchors[pinname] = (arefx + i*pinspace, top)

        bot = .11*pictorial.INCH
        botx = 1.23*pictorial.INCH
        for i, pinname in enumerate(['ioref', 'reset', 'threev3',
                                    'fivev', 'gnd1', 'gnd2', 'vin']):
            self.anchors[pinname] = (botx + i*pinspace, bot)

        botx += i*pinspace + pictorial.PINSPACING*2
        for i, pinname in enumerate(['A0', 'A1', 'A2', 'A3', 'A4', 'A5']):
            self.anchors[pinname] = (botx + i*pinspace, bot)


with schemdraw.Drawing(show=False, file='../assets/level_shifter_bb.svg') as d:
    ard = ArduinoUno()
    d += ard
    bb = pictorial.Breadboard().at((0, 9)).up()
    d += bb
    
    transistor = pictorial.TO92().at(bb.J19)
    d += transistor
    d += elm.Wire('n', k=-1).at(ard.gnd1).to(bb.L2_28)
    d += elm.Wire('n', k=-1.5).at(ard.fivev).to(bb.L1_29).color('red')
    d += elm.Wire('|-',k=1).at(ard.pin8).to(bb.G19).color('green')

    resistor_4_7k = pictorial.Resistor(4700).at(bb.E19).to(bb.F19)
    d += resistor_4_7k.label('4.7kΩ', loc='bottom', ofst=0.2)
    d += elm.Wire().at(bb.L1_20).to(bb.A19).color('red')

    d += elm.Wire('-|').at(bb.G21).to(bb.L2_27)

    resistor_1k = pictorial.Resistor(100).at(bb.I20).to(bb.I30)
    d += resistor_1k.label('1kΩ', loc='top', ofst=0.2)

    d += elm.Line().at(bb.H30).right().label('SDIO', loc='right')
    d += elm.Line().at(bb.L2_29).right().label('Sensor GND', loc='right')