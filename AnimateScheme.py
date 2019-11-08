import math
from typing import List
from svgwrite import *


def demo():
    dwg = Drawing()
    dwg.add(dwg.line((0, 0), (1, 1)))
    dwg.write(open('tmp.svg', 'w', encoding='utf-8'))


if __name__ == '__main__':
    demo()
