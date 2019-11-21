import math
from typing import List
from svgwrite import *


def demo():
    dwg = Drawing()
    symbol = dwg.defs.add(dwg.symbol(id="resistor", viewBox="0 0 50 20",
                                     style="fill:none; stroke:black; stroke-width:8"))
    symbol.add(dwg.rect(insert=(0, 0), size=(50, 20)))

    dwg.add(dwg.use(href='#resistor', insert=(100, 100), size=(50, 20)))
    dwg.add(dwg.use(href='#resistor', insert=(200, 100), size=(50, 20)))
    dwg.add(dwg.line(start=(50, 110), end=(100, 110), style='stroke:black; stroke-width:4'))
    dwg.add(dwg.line(start=(150, 110), end=(200, 110), style='stroke:black; stroke-width:4'))
    dwg.add(dwg.line(start=(250, 110), end=(300, 110), style='stroke:black; stroke-width:4'))
    dwg.write(open('tmp.svg', 'w', encoding='utf-8'))


if __name__ == '__main__':
    demo()
