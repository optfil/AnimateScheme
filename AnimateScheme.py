import math
from typing import List
from svgwrite import *


def demo():
    dwg = Drawing()
    square = dwg.add(dwg.rect((0, 0), (50, 20), fill='none', stroke='black', stroke_width=2))
    dwg.write(open('tmp.svg', 'w', encoding='utf-8'))


if __name__ == '__main__':
    demo()
