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
contact_width: int = 10
contact_size: int = 50
grounding_width: int = 100
grounding_height: int = 60
line_width: int = 6


def unite_bounding_boxes(boxes: List[BoundBox]) -> BoundBox:
    if not boxes:
        return (0, 0), (0, 0)

    box: BoundBox = boxes[0]
    for b in boxes[1:]:
        box = (min(box[0][0], b[0][0]), min(box[0][1], b[0][1])), (max(box[1][0], b[1][0]), max(box[1][1], b[1][1]))
    return box


@dataclass(frozen=True)
class AxisTransform:
    class ReverseState(Enum):
        STRAIGHT = 1
        REVERSED = -1

    scale: float = 1.0
    x_shift: float = 0.0
    y_shift: float = 0.0
    x_reversed: ReverseState = ReverseState.STRAIGHT
    y_reversed: ReverseState = ReverseState.REVERSED

    def x(self, x_old: RealCoord) -> RealCoord:
        return x_old * self.scale * self.x_reversed.value + self.x_shift

    def y(self, y_old: RealCoord) -> RealCoord:
        return y_old * self.scale * self.y_reversed.value + self.y_shift

    def xy(self, x_old: RealCoord, y_old: RealCoord) -> Tuple[RealCoord, RealCoord]:
        return self.x(x_old), self.y(y_old)

    @classmethod
    def build(cls, bbox: BoundBox, image_size: Tuple[int, int]) -> AxisTransform:
        scale: float = min(image_size[0] / (bbox[1][0] - bbox[0][0]), image_size[1] / (bbox[1][1] - bbox[0][1]))
        x_shift: float = 0.5 * (image_size[0] - scale * (bbox[1][0] + bbox[0][0]))
        y_shift: float = 0.5 * (image_size[1] + scale * (bbox[1][1] + bbox[0][1]))
        return AxisTransform(scale, x_shift, y_shift)


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
        image_draw.ellipse([tr.xy(self.x - contact_size / 2, self.y - contact_size / 2),
                            tr.xy(self.x + contact_size / 2, self.y + contact_size / 2)],
                           outline=line_color, fill=background_color, width=line_width)
        image_draw.line([tr.xy(self.x - contact_size / 2, self.y - contact_size / 2),
                         tr.xy(self.x + contact_size / 2, self.y + contact_size / 2)],
                        fill=line_color, width=line_width)

    def bounding_box(self) -> BoundBox:
        return (-contact_size / 2, -contact_size / 2), \
               (+contact_size / 2, +contact_size / 2)


@dataclass
class Grounding(CircuitElement):
    def draw(self, image_draw: ImageDraw.Draw, tr: AxisTransform = AxisTransform()) -> None:
        cc: Tuple[RealCoord, RealCoord] = tr.xy(self.x, self.y)
        image_draw.line([cc, (cc[0], cc[1] + grounding_height / 3)],
                        fill=line_color, width=line_width)
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
               (+grounding_width / 2, grounding_height)


@dataclass
class Circuit:
    elements: List[CircuitElement] = field(default_factory=list)

    def add(self, element: CircuitElement) -> None:
        self.elements.append(element)

    def axis_transformation(self, image_size: Tuple[int, int],
                            x_reverse: AxisTransform.ReverseState = AxisTransform.ReverseState.STRAIGHT,
                            y_reverse: AxisTransform.ReverseState = AxisTransform.ReverseState.REVERSED) \
            -> AxisTransform:
        if not self.elements:
            return AxisTransform(0.0, 0.0, 0.0, x_reverse, y_reverse)

        x_cons: List[Constraint] = list()
        y_cons: List[Constraint] = list()
        for element in self.elements:
            pos: Tuple[float, float] = element.xy()
            bbox: BoundBox = element.bounding_box()
            x_cons.append(Constraint.make(x_reverse.value * pos[0], -bbox[0][0], image_size[0] - bbox[1][0]))
            y_cons.append(Constraint.make(y_reverse.value * pos[1], -bbox[0][1], image_size[1] - bbox[1][1]))
        print(optimization.all_valid_constraints(x_cons), optimization.has_solutions(x_cons))
        print(optimization.all_valid_constraints(y_cons), optimization.has_solutions(y_cons))
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
        if not self.elements:
            return

        bbox: BoundBox = unite_bounding_boxes([element.bounding_box() for element in self.elements])

        if bbox[1][0] == bbox[0][0] or bbox[1][1] == bbox[0][1]:
            return

        tr: AxisTransform = AxisTransform.build(bbox, image_size)
        image: Image = Image.new('RGB', image_size, background_color)
        image_draw: ImageDraw = ImageDraw.Draw(image)
        for element in self.elements:
            element.draw(image_draw, tr)

        file: BinaryIO = open(pf, 'wb') if isinstance(pf, str) else pf
        image.save(file, format='PNG')

        print(tr)
        print(bbox)
        print(tr.xy(bbox[0][0], bbox[0][1]))
        print(tr.xy(bbox[1][0], bbox[1][1]))
