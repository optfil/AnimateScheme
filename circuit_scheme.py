from __future__ import annotations

import math
from typing import Tuple, List, Union, BinaryIO
from dataclasses import dataclass, field
from PIL import Image, ImageDraw
from abc import ABC, abstractmethod
from enum import Enum

from optimization import Constraint, solve
import optimization


RealCoord = float
BoundBox = Tuple[Tuple[RealCoord, RealCoord], Tuple[RealCoord, RealCoord]]
Color = Tuple[int, int, int]


line_color: Color = (0, 0, 0)  # black
background_color: Color = (255, 255, 255)  # white
contact_radius: float = 50
grounding_width: float = 100
grounding_height: float = 60
node_radius: float = 16
line_width: int = 8
wire_width: int = 6


@dataclass(frozen=True)
class AxisTransform:
    class ReverseState(Enum):
        STRAIGHT = 1
        REVERSED = -1

    scale_: float = 1.0
    x_shift_: float = 0.0
    y_shift_: float = 0.0
    x_reversed_: ReverseState = ReverseState.STRAIGHT
    y_reversed_: ReverseState = ReverseState.REVERSED

    def x(self, x_old: RealCoord) -> RealCoord:
        return x_old * self.scale_ * self.x_reversed_.value + self.x_shift_

    def y(self, y_old: RealCoord) -> RealCoord:
        return y_old * self.scale_ * self.y_reversed_.value + self.y_shift_

    def xy(self, x_old: RealCoord, y_old: RealCoord) -> Tuple[RealCoord, RealCoord]:
        return self.x(x_old), self.y(y_old)

    def x_reversed(self) -> ReverseState:
        return self.x_reversed_

    def y_reversed(self) -> ReverseState:
        return self.y_reversed_


@dataclass
class CircuitElement(ABC):
    x: RealCoord
    y: RealCoord

    @abstractmethod
    def draw(self, image_draw: ImageDraw.Draw, tr: AxisTransform = AxisTransform()) -> None:
        pass

    def xy(self) -> Tuple[float, float]:
        return self.x, self.y

    @abstractmethod
    def bounding_box(self) -> BoundBox:
        pass


@dataclass
class Contact(CircuitElement):
    def draw(self, image_draw: ImageDraw.Draw, tr: AxisTransform = AxisTransform()) -> None:
        cc: Tuple[RealCoord, RealCoord] = tr.xy(self.x, self.y)
        image_draw.ellipse([(cc[0] - contact_radius / 2, cc[1] - contact_radius / 2),
                            (cc[0] + contact_radius / 2, cc[1] + contact_radius / 2)],
                           outline=line_color, fill=background_color, width=line_width)
        image_draw.line([(cc[0] - contact_radius * 0.6, cc[1] + contact_radius * 0.6),
                         (cc[0] + contact_radius * 0.6, cc[1] - contact_radius * 0.6)],
                        fill=line_color, width=line_width)

    def bounding_box(self) -> BoundBox:
        return (-contact_radius * 0.6 - line_width / 2 / math.sqrt(2),
                -contact_radius * 0.6 - line_width / 2 / math.sqrt(2)), \
               (+contact_radius * 0.6 + line_width / 2 / math.sqrt(2),
                +contact_radius * 0.6 + line_width / 2 / math.sqrt(2))


@dataclass
class Grounding(CircuitElement):
    def draw(self, image_draw: ImageDraw.Draw, tr: AxisTransform = AxisTransform()) -> None:
        cc: Tuple[RealCoord, RealCoord] = tr.xy(self.x, self.y)
        image_draw.line([cc, (cc[0], cc[1] + grounding_height / 3)],
                        fill=line_color, width=wire_width)
        image_draw.line([(cc[0] - grounding_width / 2, cc[1] + grounding_height / 3),
                         (cc[0] + grounding_width / 2, cc[1] + grounding_height / 3)],
                        fill=line_color, width=line_width)
        image_draw.line([(cc[0] - grounding_width / 3, cc[1] + grounding_height / 3 * 2),
                         (cc[0] + grounding_width / 3, cc[1] + grounding_height / 3 * 2)],
                        fill=line_color, width=line_width)
        image_draw.line([(cc[0] - grounding_width / 6, cc[1] + grounding_height),
                         (cc[0] + grounding_width / 6, cc[1] + grounding_height)],
                        fill=line_color, width=line_width)

    def bounding_box(self) -> BoundBox:
        return (-grounding_width / 2, 0), \
               (+grounding_width / 2, grounding_height + line_width / 2)


@dataclass
class Node(CircuitElement):
    def draw(self, image_draw: ImageDraw.Draw, tr: AxisTransform = AxisTransform()) -> None:
        cc: Tuple[RealCoord, RealCoord] = tr.xy(self.x, self.y)
        image_draw.ellipse([(cc[0] - node_radius / 2, cc[1] - node_radius / 2),
                            (cc[0] + node_radius / 2, cc[1] + node_radius / 2)],
                           outline=line_color, fill=line_color, width=line_width)

    def bounding_box(self) -> BoundBox:
        return (-node_radius * 0.5, -node_radius * 0.5), (node_radius * 0.5, node_radius * 0.5)


@dataclass
class Wire:
    nodes_: List[Tuple[RealCoord, RealCoord]]

    def nodes(self) -> List[Tuple[RealCoord, RealCoord]]:
        return self.nodes_

    def draw(self, image_draw: ImageDraw.Draw, tr: AxisTransform = AxisTransform()) -> None:
        if len(self.nodes_) < 2:
            return

        nodes_positions: List[Tuple[RealCoord, RealCoord]] = [tr.xy(node[0], node[1]) for node in self.nodes_]
        image_draw.line(nodes_positions,
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

    def axis_transformation(self, image_size: Tuple[int, int],
                            x_reverse: AxisTransform.ReverseState = AxisTransform.ReverseState.STRAIGHT,
                            y_reverse: AxisTransform.ReverseState = AxisTransform.ReverseState.REVERSED) \
            -> AxisTransform:
        if not self.elements_:
            return AxisTransform(0.0, 0.0, 0.0, x_reverse, y_reverse)

        x_cons: List[Constraint] = list()
        y_cons: List[Constraint] = list()
        for element in self.elements_:
            pos: Tuple[float, float] = element.xy()
            bbox: BoundBox = element.bounding_box()
            x_cons.append(Constraint.make(x_reverse.value * pos[0], -bbox[0][0], image_size[0] - bbox[1][0]))
            y_cons.append(Constraint.make(y_reverse.value * pos[1], -bbox[0][1], image_size[1] - bbox[1][1]))
        for wire in self.wires_:
            for node in wire.nodes():
                x_cons.append(Constraint.make(x_reverse.value * node[0], wire_width / 2,
                                              image_size[0] - wire_width / 2))
                y_cons.append(Constraint.make(y_reverse.value * node[1], wire_width / 2,
                                              image_size[1] - wire_width / 2))
        sx: float
        dx: float
        sx, dx = solve(x_cons)
        print(sx, dx)
        sy: float
        dy: float
        sy, dy = solve(y_cons)
        print(sy, dy)

        if math.isinf(sx) and math.isinf(sy):
            return AxisTransform(1.0, 0.0, 0.0, x_reverse, y_reverse)

        s: float
        if sx < sy:
            s = sx
            dy = optimization.dx_interval_mid(y_cons, s)
        else:
            s = sy
            dx = optimization.dx_interval_mid(x_cons, s)

        print(s, dx, dy)
        return AxisTransform(s, dx, dy, x_reverse, y_reverse)

    def save_png(self, image_size: Tuple[int, int], pf: Union[BinaryIO, str]) -> None:
        if not self.elements_:
            return

        tr: AxisTransform = self.axis_transformation(image_size)
        image: Image = Image.new('RGB', image_size, background_color)
        image_draw: ImageDraw = ImageDraw.Draw(image)
        for wire in self.wires_:
            wire.draw(image_draw, tr)
        for element in self.elements_:
            element.draw(image_draw, tr)

        file: BinaryIO = open(pf, 'wb') if isinstance(pf, str) else pf
        image.save(file, format='PNG')
