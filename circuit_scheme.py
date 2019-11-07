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


@dataclass
class CircuitElement(ABC):
    x_: IntCoord
    y_: IntCoord

    @abstractmethod
    def draw(self, image_draw: ImageDraw.Draw) -> None:
        pass

    @abstractmethod
    def bounding_box(self) -> BoundBox:
        pass


@dataclass
class Contact(CircuitElement):
    def draw(self, image_draw: ImageDraw.Draw) -> None:
        image_draw.ellipse([(self.x_ - contact_diameter / 2, self.y_ - contact_diameter / 2),
                            (self.x_ + contact_diameter / 2, self.y_ + contact_diameter / 2)],
                           outline=line_color, fill=background_color, width=line_width)
        image_draw.line([(self.x_ - contact_diameter * 0.6, self.y_ + contact_diameter * 0.6),
                         (self.x_ + contact_diameter * 0.6, self.y_ - contact_diameter * 0.6)],
                        fill=line_color, width=line_width)

    def bounding_box(self) -> BoundBox:
        return (math.floor(-contact_diameter * 0.6 - line_width / 2 / math.sqrt(2)),
                math.floor(-contact_diameter * 0.6 - line_width / 2 / math.sqrt(2))), \
               (math.ceil(contact_diameter * 0.6 + line_width / 2 / math.sqrt(2)),
                math.ceil(contact_diameter * 0.6 + line_width / 2 / math.sqrt(2)))


@dataclass
class Grounding(CircuitElement):
    def draw(self, image_draw: ImageDraw.Draw) -> None:
        image_draw.line([(self.x_, self.y_), (self.x_, self.y_ + grounding_height / 3)],
                        fill=line_color, width=wire_width)
        image_draw.line([(self.x_ - grounding_width / 2, self.y_ + grounding_height / 3),
                         (self.x_ + grounding_width / 2, self.y_ + grounding_height / 3)],
                        fill=line_color, width=line_width)
        image_draw.line([(self.x_ - grounding_width / 3, self.y_ + grounding_height / 3 * 2),
                         (self.x_ + grounding_width / 3, self.y_ + grounding_height / 3 * 2)],
                        fill=line_color, width=line_width)
        image_draw.line([(self.x_ - grounding_width / 6, self.y_ + grounding_height),
                         (self.x_ + grounding_width / 6, self.y_ + grounding_height)],
                        fill=line_color, width=line_width)

    def bounding_box(self) -> BoundBox:
        return (math.floor(-grounding_width / 2), 0), \
               (math.ceil(grounding_width / 2), math.ceil(grounding_height + line_width / 2))


@dataclass
class Node(CircuitElement):
    def draw(self, image_draw: ImageDraw.Draw) -> None:
        image_draw.ellipse([(self.x_ - node_radius / 2, self.y_ - node_radius / 2),
                            (self.x_ + node_radius / 2, self.y_ + node_radius / 2)],
                           outline=line_color, fill=line_color, width=line_width)

    def bounding_box(self) -> BoundBox:
        return (math.floor(-node_radius * 0.5), math.floor(-node_radius * 0.5)), \
               (math.ceil(node_radius * 0.5), math.ceil(node_radius * 0.5))


@dataclass
class Resistance(CircuitElement):
    angle_: float = 0.0

    def draw(self, image_draw: ImageDraw.Draw) -> None:
        def rotate(x: float, y: float, a: float) -> Tuple[float, float]:
            return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)

        x_min: float = self.x_ - resistance_length / 2
        x_max: float = self.x_ + resistance_length / 2
        y_min: float = self.y_ - resistance_width / 2
        y_max: float = self.y_ + resistance_width / 2
        image_draw.line([rotate(x_min, y_min, self.angle_), rotate(x_max, y_min, self.angle_),
                         rotate(x_max, y_max, self.angle_), rotate(x_min, y_max, self.angle_),
                         rotate(x_min, y_min, self.angle_), rotate(x_max, y_min, self.angle_)],
                        fill=line_color, width=line_width, joint='curve')

    def bounding_box(self) -> BoundBox:
        return (math.floor(-node_radius * 0.5), math.floor(-node_radius * 0.5)), \
               (math.ceil(node_radius * 0.5), math.ceil(node_radius * 0.5))


@dataclass
class Wire:
    nodes_: List[Tuple[IntCoord, IntCoord]]

    def nodes(self) -> List[Tuple[IntCoord, IntCoord]]:
        return self.nodes_

    def draw(self, image_draw: ImageDraw.Draw) -> None:
        if len(self.nodes_) < 2:
            return

        image_draw.line(self.nodes_,
                        fill=line_color, width=wire_width, joint='curve')


@dataclass
class Circuit:
    elements_: List[CircuitElement] = field(default_factory=list)
    wires_: List[Wire] = field(default_factory=list)

    def add(self, element: Union[CircuitElement, Wire]) -> None:
        if isinstance(element, Wire):
            self.wires_.append(element)
        else:
            self.elements_.append(element)

    def save_png(self, image_size: Tuple[int, int], pf: Union[BinaryIO, str]) -> None:
        if not self.elements_:
            return

        image: Image = Image.new('RGB', image_size, background_color)
        image_draw: ImageDraw = ImageDraw.Draw(image)
        for wire in self.wires_:
            wire.draw(image_draw)
        for element in self.elements_:
            element.draw(image_draw)

        file: BinaryIO = open(pf, 'wb') if isinstance(pf, str) else pf
        image.save(file, format='PNG')
