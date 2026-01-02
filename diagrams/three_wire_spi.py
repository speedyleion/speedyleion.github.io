import schemdraw
import schemdraw.elements as elm
from schemdraw.elements.intcircuits import Ic, IcPin
import schemdraw.logic as logic
from schemdraw.util import Point

class Controller(Ic):
    def __init__(self, cs_count=1, **kwargs):

        pins = []
        if cs_count == 1:
            pins.append(IcPin(name=f'CS', side='right'))
        else:
            cs_pins = [IcPin(name=f'CS{i}', side='right') for i in range(1, cs_count + 1)]
            cs_pins.reverse()
            pins.extend(cs_pins)

        pins.extend((
        IcPin(name='DATA', side='right'),
        IcPin(name='CLK', side='right'),
        IcPin(name='GND', side='right'),
        )
        )
        super().__init__(pins=pins, botlabel='Controller')


class Peripheral(Ic):
    def __init__(self, name='Peripheral', **kwargs):
        pins=[
        IcPin(name='CS', side='left'),
        IcPin(name='DATA', side='left'),
        IcPin(name='CLK', side='left'),
        IcPin(name='GND', side='left'),
        ]
        super().__init__(pins=pins, botlabel=name)

with schemdraw.Drawing(show=False, file='../assets/three_wire_spi.svg') as d:
    controller = Controller()
    d += controller
    d += elm.lines.Line().at(controller.CLK).right()

    peripheral = Peripheral()
    d += peripheral.anchor('CLK')
    
    d += elm.lines.Wire('-|').at(controller.DATA).to(peripheral.DATA)
    d += elm.lines.Wire('-|').at(controller.CS).to(peripheral.CS)
    d += elm.lines.Wire('-|').at(controller.GND).to(peripheral.GND)


with schemdraw.Drawing(show=False, file='../assets/clock_signal.svg') as d:
    logic.TimingDiagram({
        'signal': [
            {'name': 'clk', 'wave': 'p......'},  
        ]
    })

with schemdraw.Drawing(show=False, file='../assets/three_wire_spi_data_signal.svg') as d:
    logic.TimingDiagram({
        'signal': [
            {'name': 'clk', 'wave': 'p......'},  
            {'name': 'data', 'wave': 'x.==.x.', 'data': ['request', 'response']},
            {'name': 'cs', 'wave': '0.1..0.'}]})

with schemdraw.Drawing(show=False, file='../assets/three_wire_spi_multiple_peripherals.svg') as d:
    drop_offset = 0.15
    controller = Controller(cs_count=3)
    d += controller
    gnd_drop = elm.lines.Line().at(controller.GND).right(d.unit * drop_offset * 2).dot()
    d += gnd_drop
    clk_drop = elm.lines.Line().at(controller.CLK).right(d.unit * drop_offset * 3).dot()
    d += clk_drop
    data_drop = elm.lines.Line().at(controller.DATA).right(d.unit * drop_offset * 4).dot()
    d += data_drop

    d += elm.lines.Line().at(gnd_drop.end).right(d.unit * (1 - (drop_offset * 2)))

    peripheral1 = Peripheral(name='Peripheral 1').right()
    d += peripheral1.anchor('GND')
    
    d += elm.lines.Wire('|-').at(data_drop.end).to(peripheral1.DATA)
    d += elm.lines.Wire('|-').at(clk_drop.end).to(peripheral1.CLK)
    d += elm.lines.Wire('|-').at(controller.CS1).to(peripheral1.CS)

    bbox = peripheral1.get_bbox()
    offset = Point((0, -(bbox.ymax - bbox.ymin) * 1.2))

    peripheral2 = Peripheral(name='Peripheral 2').right()
    d += peripheral2.at(peripheral1.CLK + offset).anchor('CLK')
    d += elm.lines.Line().at(controller.CS2).right(d.unit * drop_offset)
    d += elm.lines.Wire('|-').to(peripheral2.CS)
    d += elm.lines.Line().left().at(peripheral2.GND).tox(gnd_drop.end.x).dot()
    d += elm.lines.Line().left().at(peripheral2.DATA).tox(data_drop.end.x).dot()
    d += elm.lines.Line().left().at(peripheral2.CLK).tox(clk_drop.end.x).dot()
    
    peripheral3 = Peripheral(name='Peripheral 3').right()
    d += peripheral3.at(peripheral2.CLK + offset).anchor('CLK')
    d += elm.lines.Wire('|-').at(controller.CS3).to(peripheral3.CS)
    d += elm.lines.Wire('|-').at(gnd_drop.end).to(peripheral3.GND)
    d += elm.lines.Wire('|-').at(data_drop.end).to(peripheral3.DATA)
    d += elm.lines.Wire('|-').at(clk_drop.end).to(peripheral3.CLK)
    

with schemdraw.Drawing(show=False, file='../assets/clock_polarity.svg') as d:
    logic.TimingDiagram({
        'signal': [
            {'name': 'low_polarity', 'wave': '0.p......'},  
            {'name': 'high_polarity', 'wave': '1.n......'},  
        ],
    'edge': [
        '[0^:0]+[0^:1.9] idle',
        '[0^:1.9]+[0^:8.9] signal',
        '[1v:0]+[1v:1.9] idle',
        '[1v:1.9]+[1v:8.9] signal',
        ],
    },
    ygap=0.5
    )

with schemdraw.Drawing(show=False, file='../assets/low_polarity_cpha0.svg') as d:
    logic.TimingDiagram({
        'signal': [
            {'name': 'clk', 'wave': 'p........'},  
            {
                'name': 'data', 
                'wave': 'x========x', 
                'data': ['b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8'],
                'async': [0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9],
                },
        ],
        'edge': [
            '[0^:0.5]+[1v:0.5]{blue} write',
            '[1v:2]+[0^:2]{red} read',
        ],
        },
        grid=False,
    ygap=0.5
        )