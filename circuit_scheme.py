from typing import Tuple
from dataclasses import dataclass
import PIL


line_color: Tuple[int, ...] = (0, 0, 0)  # black
background_color: Tuple[int, ...] = (255, 255, 255)  # white
contact_width: int = 10
contact_size: int = 50
grounding_width: int = 100
grounding_height: int = 60
line_width: int = 6


@dataclass
class CircuitElement:
    pass


@dataclass
class AxisTransform:
    scale: float = 1.0
    x_shift: float = 0.0
    y_shift: float = 0.0
    x_reverse: bool = False
    y_reverse: bool = True

    def x(self, x_old: float) -> float:
        return (x_old * self.scale + self.x_shift) * self.x_reverse

    def y(self, y_old: float) -> float:
        return (y_old * self.scale + self.y_shift) * self.y_reverse

    def xy(self, x_old: float, y_old: float) -> Tuple[float, float]:
        return self.x(x_old), self.y(y_old)

    def xy(self, xy_old: Tuple[float, float]) -> Tuple[float, float]:
        return self.xy(xy_old[0], xy_old[1])


@dataclass
class Contact(CircuitElement):
    x: float
    y: float

    def xy(self) -> Tuple[float, float]:
        return self.x, self.y

    def draw(self, image_draw: PIL.ImageDraw, tr: AxisTransform = AxisTransform(),
             size=contact_size, color=line_color, fill=background_color, width=line_width) -> None:
        image_draw.ellipse([tr.xy(self.x - size / 2, self.y - size / 2), tr.xy(self.x + size / 2, self.y + size / 2)],
                           outline=color, fill=fill, width=width)
        image_draw.line([tr.xy(self.x - size / 2, self.y + size / 2), tr.xy(self.x + size / 2, self.y - size / 2)],
                        fill=color, width=width)


@dataclass
class Grounding(CircuitElement):
    x: float
    y: float

    def xy(self) -> Tuple[float, float]:
        return self.x, self.y

    def draw(self, image_draw: PIL.ImageDraw, tr: AxisTransform = AxisTransform(),
             color=line_color, width=line_width) -> None:
        image_draw.line([tr.xy(self.x, self.y), tr.xy(self.x, self.y + grounding_height / 3)],
                        fill=color, width=width)
        image_draw.line([tr.xy(self.x - grounding_width / 2, self.y + grounding_height / 3),
                         tr.xy(self.x + grounding_width / 2, self.y + grounding_height / 3)],
                        fill=color, width=width)
        image_draw.line([tr.xy(self.x - grounding_width / 3, self.y + grounding_height / 3 * 2),
                         tr.xy(self.x + grounding_width / 3, self.y + grounding_height / 3 * 2)],
                        fill=color, width=width)
        image_draw.line([tr.xy(self.x - grounding_width / 6, self.y + grounding_height),
                         tr.xy(self.x + grounding_width / 6, self.y + grounding_height)],
                        fill=color, width=width)
