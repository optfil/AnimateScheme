from PIL import Image, ImageDraw


image_resize_factor = 0.1
image_width = 3300
image_height = 2400
resistor_length = 500
resistor_width = 200
resistor_outline_width = 1  # 10 * image_resize_factor
wire_outline_width = 1  # 6 * image_resize_factor


def c_x(x):
    return image_resize_factor * (x + image_width/2)


def c_y(y):
    return image_resize_factor * (y + image_height/2)


def create_empty_frame():
    return Image.new('RGB', (int(image_width * image_resize_factor), int(image_height * image_resize_factor)), (255, 255, 255))


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

    draw.line(xy_new, width=wire_outline_width, fill=(0, 0, 0), joint='curve')


def create_frame_stage_1(step, max_steps):
    img = create_empty_frame()
    draw = ImageDraw.Draw(img)

    draw_resistor(draw, 0, 0)
    draw_resistor(draw, -900, 0)
    draw_resistor(draw, 900, 0)

    draw_wire(draw, [250, 0, 650, 0])
    draw_wire(draw, [-250, 0, -650, 0])
    draw_wire(draw, [1150, 0, 1350, 0])
    draw_wire(draw, [-1150, 0, -1350, 0])
    draw_wire(draw, [-450, 0, -450, 900, 1350, 900, 1350, 0])
    draw_wire(draw, [450, 0, 450, -900, -1350, -900, -1350, 0])

    turn_step = int(max_steps * 6.0 / 17.0)
    if step <= turn_step:
        x1 = 1550
        y1 = 1100 * step / turn_step
        x2 = 1350
        y2 = 900 * step / turn_step
        draw_wire(draw, [x1, y1, x2, y2])
        draw_wire(draw, [-x1, -y1, -x2, -y2])
    else:
        x1 = 1550 - 1100 * (step-turn_step) / (max_steps - 1 - turn_step)
        y1 = 1150
        x2 = 1350 - 900 * (step-turn_step) / (max_steps - 1 - turn_step)
        y2 = 900
        draw_wire(draw, [x1, y1, x2, y2])
        draw_wire(draw, [-x1, -y1, -x2, -y2])

    return img


def create_frame_stage_2(step, max_steps):
    img = create_empty_frame()
    draw = ImageDraw.Draw(img)

    draw_resistor(draw, 0, 0)
    draw_resistor(draw, -900, 0)

    draw_wire(draw, [-250, 0, -650, 0])
    draw_wire(draw, [-1150, 0, -1350, 0])
    draw_wire(draw, [450, 600, 450, 400])
    draw_wire(draw, [-450, -600, -450, -400])
    draw_wire(draw, [450, 0, 450, -400, -1350, -400, -1350, 0])

    draw_resistor(draw, 900, 0)
    draw_wire(draw, [250, 0, 650, 0])
    draw_wire(draw, [1150, 0, 1350, 0])
    draw_wire(draw, [-450, 0, -450, 400, 1350, 400, 1350, 0])

    return img


if __name__ == '__main__':
    frames = []
    for n_frame in range(100):
        frames.append(create_frame_stage_1(n_frame, 100))

    # for n_frame in range(10):
    #     frames.append(create_frame_stage_2(n_frame, 10))

    # frames = [frame.resize((image_width, image_height), resample=Image.LANCZOS) for frame in frames]
    frames[0].save('scheme_transformation.gif', format='GIF', append_images=frames[1:], save_all=True,
                   duration=20, loop=1)
