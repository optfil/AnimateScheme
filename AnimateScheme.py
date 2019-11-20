import math
from typing import List
from svgwrite import *


def demo():
    dwg = Drawing()
    square = dwg.add(dwg.rect(insert=(0, 0), size=(50, 20), style='fill:none; stroke:red; stroke-width:2'))
    dwg.write(open('tmp.svg', 'w', encoding='utf-8'))


if __name__ == '__main__':
    demo()
