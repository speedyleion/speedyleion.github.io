# Lonely Binary logic analyzer break out board for use with schemdraw pictorial
# views

import schemdraw
import schemdraw.elements as elm
import schemdraw.pictorial as pictorial


class LonelyBinary(elm.ElementImage):
    WIDTH = 726
    HEIGHT = 421
    GROUND_OFFSET = (39, 152)
    Y_OFFSET = 124
    def __init__(self):
        pinspace = pictorial.PINSPACING

        width = 6.2
        height = width * (self.HEIGHT / self.WIDTH)
        super().__init__('lonely-binary-bb.png', width=width, height=height, xy=(0, 0))

        x0 = width * (self.GROUND_OFFSET[0] / self.WIDTH)
        y_bot = height * (self.GROUND_OFFSET[1] / self.HEIGHT)
        y_top = height * ((self.GROUND_OFFSET[1] + self.Y_OFFSET) / self.HEIGHT)

        names = ['GND', 'CLK', '7', '6', '5', '4', '3', '2', '1', '0']
        for i, name in enumerate(names):
            self.anchors[name] = (x0 + i * pinspace, y_bot)
            self.anchors[f'{name}_top'] = (x0 + i * pinspace, y_top)

if __name__ == '__main__':
    with schemdraw.Drawing() as d:
        bb = pictorial.Breadboard().up()
        d += bb

        lb = LonelyBinary().at(bb.F30).anchor('0_top')
        d += lb

        d += elm.Line().at(lb.GND).to(bb.A21)
        d += elm.Line().at(lb.CLK_top).to(bb.J22)
        d += elm.Line().at(getattr(lb, '0_top')).to(bb.J30)
        
