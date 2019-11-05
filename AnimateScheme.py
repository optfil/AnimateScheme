from PIL import Image, ImageDraw


image_width = 330
image_height = 140
resistor_length = 50
resistor_width = 20
resistor_outline_width = 3
wire_outline_width = 1


def c_x(x):
    return x + image_width/2


def c_y(y):
    return y + image_height/2


def draw_resistor(draw, x_center, y_center):
    draw.rectangle(
        [c_x(x_center - resistor_length / 2), c_y(y_center - resistor_width / 2),
         c_x(x_center + resistor_length / 2), c_y(y_center + resistor_width / 2)],
        outline=(0, 0, 0), width=resistor_outline_width)


def draw_wire(draw, xy):
    if not xy:
        return

    xy_new = xy
    if not isinstance(xy_new[0], tuple):
        xy_new = [(xy[i], xy[i+1]) for i in range(0, len(xy), 2)]
    xy_new = [(c_x(elem[0]), c_y(elem[1])) for elem in xy_new]

    draw.line(xy_new, wire_outline_width)


def create_frame_stage_1(step, maxsteps):
    img = Image.new('RGB', (image_width, image_height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw_resistor(draw, 0, 0)
    draw_resistor(draw, -90, 0)
    draw_resistor(draw, 90, 0)

    draw_wire(draw, [25, 0, 65, 0])
    draw_wire(draw, [(-25, 0,), (-65, 0)])
    draw_wire(draw, [])

    return img


if __name__ == '__main__':
    frames = []
    frames.append(create_frame_stage_1(0, 0))
    frames[0].save('scheme_transformation.gif', format='GIF', append_images=frames[1:], save_all=True, duration=100, loop=1)
