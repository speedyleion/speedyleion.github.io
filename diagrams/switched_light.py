import schemdraw
import schemdraw.elements as elm

with schemdraw.Drawing(show=False, file='../assets/switched_light.svg') as d:
    # Note: reversing battery to have + at top
    battery = elm.Battery().reverse().up().label(['$-$ ', 'Battery', ' +'])
    elm.Line().right(d.unit*.75)
    switch = elm.Switch().label('Switch')
    elm.Line().right(d.unit*.75)
    d += elm.Lamp().down().label('Light')
    elm.Line().left(d.unit*.75).to(battery.start)


with schemdraw.Drawing(show=False, file='../assets/closed_switched_light.svg') as d:
    # Note: reversing battery to have + at top
    battery = elm.Battery().reverse().up().label(['$-$ ', 'Battery', ' +'])
    elm.Line().right(d.unit*.75)
    switch = elm.Switch(nc=True).label('Switch')
    elm.Line().right(d.unit*.75)
    d += elm.Lamp(filament_color='gold').down().label('Light')
    elm.Line().left(d.unit*.75).to(battery.start)
