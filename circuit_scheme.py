from __future__ import annotations

import math
from typing import Tuple, List, Union, BinaryIO
from dataclasses import dataclass, field
from PIL import Image, ImageDraw
from abc import ABC, abstractmethod


IntCoord = int
BoundBox = Tuple[Tuple[IntCoord, IntCoord], Tuple[IntCoord, IntCoord]]
Color = Tuple[int, int, int]


line_color: Color = (0, 0, 0)  # black
background_color: Color = (255, 255, 255)  # white
contact_diameter: int = 50
grounding_width: int = 100
grounding_height: int = 60
node_radius: int = 16
resistance_length = 150
resistance_width = 60
line_width: int = 8
wire_width: int = 6


def unite_bbox(boxes: List[BoundBox]):
    if not boxes:
        return BoundBox((math.inf, math.inf), (-math.inf, -math.inf))
    result: BoundBox = boxes[0]
    for b in boxes[1:]:
        result = (min(result[0][0], b[0][0]), min(result[0][1], b[0][1])), \
                 (max(result[1][0], b[1][0]), max(result[1][1], b[1][1]))
    return result


@dataclass
class AxisTransformation:
    x_shift_: IntCoord = 0
    y_shift_: IntCoord = 0
    x_reversed_: bool = False
    y_reversed_: bool = True

    def x(self, x_old: IntCoord) -> IntCoord:
        return x_old * int(1 - self.x_reversed_ * 2) + self.x_shift_

    def y(self, y_old: IntCoord) -> IntCoord:
        return y_old * int(1 - self.y_reversed_ * 2) + self.y_shift_

    def xy(self, xy_old: Tuple[IntCoord, IntCoord]) -> Tuple[IntCoord, IntCoord]:
        return self.x(xy_old[0]), self.y(xy_old[1])


@dataclass
class CircuitElement(ABC):
    class TerminalException(Exception):
        def __init__(self, element: CircuitElement, n_requested: int):
            self.element_ = element
            self.n_requested_ = n_requested
            super().__init__('Not enough terminals in {}: {} in total, requested {}'
                             .format(element, element.terminal_number(), n_requested))

        def __reduce__(self):
            return CircuitElement.TerminalException, (self.element_, self.n_requested_)

    x_: IntCoord
    y_: IntCoord

    def xy(self, tr: AxisTransformation = AxisTransformation()) -> Tuple[IntCoord, IntCoord]:
        return tr.xy((self.x_, self.y_))

    @abstractmethod
    def terminal_number(self) -> int:
        pass

    def terminal_position(self, n: int, tr: AxisTransformation = AxisTransformation()) -> Tuple[IntCoord, IntCoord]:
        if n >= self.terminal_number():
            raise CircuitElement.TerminalException(self, n)
        return tr.xy(self.terminal_position(n))

    @abstractmethod
    def terminal_position_(self, n: int) -> Tuple[IntCoord, IntCoord]:
        pass

    @abstractmethod
    def draw(self, image_draw: ImageDraw.Draw, tr: AxisTransformation) -> None:
        pass

    @abstractmethod
    def bounding_box_(self) -> BoundBox:
        pass

    def bounding_box(self, tr: AxisTransformation = AxisTransformation()) -> BoundBox:
        xy = tr.xy((self.x_, self.y_))
        bbox: BoundBox = self.bounding_box_()
        return (bbox[0][0] + xy[0], bbox[0][1] + xy[1]), (bbox[1][0] + xy[0], bbox[1][1] + xy[1])


@dataclass
class Terminal:
    element_: CircuitElement
    number_: int

    def xy(self, tr: AxisTransformation) -> Tuple[IntCoord, IntCoord]:
        return tr.xy(self.element_.terminal_position(self.number_))


@dataclass
class Contact(CircuitElement):
    def terminal_number(self) -> int:
        return 1

    def terminal_position_(self, n: int) -> Tuple[IntCoord, IntCoord]:
        return 0, 0

    def draw(self, image_draw: ImageDraw.Draw, tr: AxisTransformation) -> None:
        xy: Tuple[IntCoord, IntCoord] = tr.xy((self.x_, self.y_))
        image_draw.ellipse([(xy[0] - contact_diameter / 2, xy[1] - contact_diameter / 2),
                            (xy[0] + contact_diameter / 2, xy[1] + contact_diameter / 2)],
                           outline=line_color, fill=background_color, width=line_width)
        image_draw.line([(xy[0] - contact_diameter * 0.6, xy[1] + contact_diameter * 0.6),
                         (xy[0] + contact_diameter * 0.6, xy[1] - contact_diameter * 0.6)],
                        fill=line_color, width=line_width)

    def bounding_box_(self) -> BoundBox:
        return (math.floor(-contact_diameter * 0.6 - line_width / 2 / math.sqrt(2)),
                math.floor(-contact_diameter * 0.6 - line_width / 2 / math.sqrt(2))), \
               (math.ceil(contact_diameter * 0.6 + line_width / 2 / math.sqrt(2)),
                math.ceil(contact_diameter * 0.6 + line_width / 2 / math.sqrt(2)))


@dataclass
class Grounding(CircuitElement):
    def terminal_number(self) -> int:
        return 1

    def terminal_position_(self, n: int) -> Tuple[IntCoord, IntCoord]:
        return 0, 0

    def draw(self, image_draw: ImageDraw.Draw, tr: AxisTransformation) -> None:
        xy: Tuple[IntCoord, IntCoord] = tr.xy((self.x_, self.y_))
        image_draw.line([(xy[0], xy[1]), (xy[0], xy[1] + grounding_height / 3)],
                        fill=line_color, width=wire_width)
        image_draw.line([(xy[0] - grounding_width / 2, xy[1] + grounding_height / 3),
                         (xy[0] + grounding_width / 2, xy[1] + grounding_height / 3)],
                        fill=line_color, width=line_width)
        image_draw.line([(xy[0] - grounding_width / 3, xy[1] + grounding_height / 3 * 2),
                         (xy[0] + grounding_width / 3, xy[1] + grounding_height / 3 * 2)],
                        fill=line_color, width=line_width)
        image_draw.line([(xy[0] - grounding_width / 6, xy[1] + grounding_height),
                         (xy[0] + grounding_width / 6, xy[1] + grounding_height)],
                        fill=line_color, width=line_width)

    def bounding_box_(self) -> BoundBox:
        return (math.floor(-grounding_width / 2), 0), \
               (math.ceil(grounding_width / 2), math.ceil(grounding_height + line_width / 2))


@dataclass
class Node(CircuitElement):
    def terminal_number(self) -> int:
        return 1

    def terminal_position_(self, n: int) -> Tuple[IntCoord, IntCoord]:
        return 0, 0

    def draw(self, image_draw: ImageDraw.Draw, tr: AxisTransformation) -> None:
        xy: Tuple[IntCoord, IntCoord] = tr.xy((self.x_, self.y_))
        image_draw.ellipse([(xy[0] - node_radius / 2, xy[1] - node_radius / 2),
                            (xy[0] + node_radius / 2, xy[1] + node_radius / 2)],
                           outline=line_color, fill=line_color, width=line_width)

    def bounding_box_(self) -> BoundBox:
        return (math.floor(-node_radius * 0.5), math.floor(-node_radius * 0.5)), \
               (math.ceil(node_radius * 0.5), math.ceil(node_radius * 0.5))


@dataclass
class Resistance(CircuitElement):
    angle_: float = 0.0

    @classmethod
    def rotate_(cls, x: float, y: float, a: float) -> Tuple[float, float]:
        return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)

    def terminal_number(self) -> int:
        return 2

    def terminal_position_(self, n: int) -> Tuple[IntCoord, IntCoord]:
        if n == 0:
            position: Tuple[float, float] = Resistance.rotate_(-resistance_length / 2, 0, self.angle_)
            return math.floor(position[0]), math.ceil(position[1])
        elif n == 1:
            position: Tuple[float, float] = Resistance.rotate_(+resistance_length / 2, 0, self.angle_)
            return math.floor(position[0]), math.ceil(position[1])

    def draw(self, image_draw: ImageDraw.Draw, tr: AxisTransformation) -> None:
        xy: Tuple[IntCoord, IntCoord] = tr.xy((self.x_, self.y_))

        x_min: float = xy[0] - resistance_length / 2
        x_max: float = xy[0] + resistance_length / 2
        y_min: float = xy[1] - resistance_width / 2
        y_max: float = xy[1] + resistance_width / 2
        image_draw.line([Resistance.rotate_(x_min, y_min, self.angle_), Resistance.rotate_(x_max, y_min, self.angle_),
                         Resistance.rotate_(x_max, y_max, self.angle_), Resistance.rotate_(x_min, y_max, self.angle_),
                         Resistance.rotate_(x_min, y_min, self.angle_), Resistance.rotate_(x_max, y_min, self.angle_)],
                        fill=line_color, width=line_width, joint='curve')

    def bounding_box_(self) -> BoundBox:
        x1, y1 = Resistance.rotate_(+resistance_length / 2, +resistance_width / 2, self.angle_)
        x2, y2 = Resistance.rotate_(-resistance_length / 2, +resistance_width / 2, self.angle_)
        x3, y3 = Resistance.rotate_(-resistance_length / 2, -resistance_width / 2, self.angle_)
        x4, y4 = Resistance.rotate_(+resistance_length / 2, -resistance_width / 2, self.angle_)
        x_min = min(x1, x2, x3, x4)
        x_max = max(x1, x2, x3, x4)
        y_min = min(y1, y2, y3, y4)
        y_max = max(y1, y2, y3, y4)

        return (math.floor(x_min), math.floor(y_min)), (math.ceil(x_max), math.ceil(y_max))


@dataclass
class Wire:
    nodes_: List[Tuple[IntCoord, IntCoord]]

    def nodes(self) -> List[Tuple[IntCoord, IntCoord]]:
        return self.nodes_

    def draw(self, image_draw: ImageDraw.Draw, tr: AxisTransformation) -> None:
        if len(self.nodes_) < 2:
            return

        nodes: List[Tuple[IntCoord, IntCoord]] = [tr.xy(node) for node in self.nodes_]
        image_draw.line(nodes,
                        fill=line_color, width=wire_width, joint='curve')

    def bounding_box(self, tr: AxisTransformation = AxisTransformation()) -> BoundBox:
        def node_bbox(node: Tuple[IntCoord, IntCoord], t: AxisTransformation):
            xy = t.xy(node)
            return (math.floor(xy[0] - wire_width / 2), math.floor(xy[1] - wire_width / 2)), \
                   (math.ceil(xy[0] + wire_width / 2), math.ceil(xy[1] + wire_width / 2))
        return unite_bbox([node_bbox(node, tr) for node in self.nodes_])


@dataclass
class Circuit:
    elements_: List[CircuitElement] = field(default_factory=list)
    wires_: List[Wire] = field(default_factory=list)

    def add(self, element: Union[CircuitElement, Wire]) -> None:
        if isinstance(element, Wire):
            self.wires_.append(element)
        else:
            self.elements_.append(element)

    def save_png(self, pf: Union[BinaryIO, str], tr: AxisTransformation = None) -> None:
        if not self.elements_:
            return

        if not tr:
            global_bbox: BoundBox = unite_bbox([element.bounding_box() for element in self.elements_] +
                                               [wire.bounding_box() for wire in self.wires_])
            tr = AxisTransformation(-global_bbox[0][0], -global_bbox[0][1])
        global_bbox: BoundBox = unite_bbox([element.bounding_box(tr) for element in self.elements_] +
                                           [wire.bounding_box(tr) for wire in self.wires_])
        image_size: Tuple[IntCoord, IntCoord] = (global_bbox[1][0], global_bbox[1][1])
        image: Image = Image.new('RGB', image_size, background_color)
        image_draw: ImageDraw = ImageDraw.Draw(image)
        for wire in self.wires_:
            wire.draw(image_draw, tr)
        for element in self.elements_:
            element.draw(image_draw, tr)

        file: BinaryIO = open(pf, 'wb') if isinstance(pf, str) else pf
        image.save(file, format='PNG')
