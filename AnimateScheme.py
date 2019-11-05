from PIL import Image, ImageDraw
import math


image_resize_factor = 1
image_width = 3300
image_height = 2400
resistor_length = 500
resistor_width = 200
contact_size = 50
resistor_outline_width = 10 * image_resize_factor
wire_outline_width = 6 * image_resize_factor


def c_x(x):
    return image_resize_factor * (x + image_width/2)


def c_y(y):
    return image_resize_factor * (y + image_height/2)


def create_empty_frame():
    return Image.new('RGB', (int(image_width * image_resize_factor), int(image_height * image_resize_factor)),
                     (255, 255, 255))


def draw_resistor(draw, x_center, y_center, color=(0, 0, 0), angle=0.0):
    if angle == 0.0:
        draw.rectangle(
            [c_x(x_center - resistor_length / 2), c_y(y_center - resistor_width / 2),
             c_x(x_center + resistor_length / 2), c_y(y_center + resistor_width / 2)],
            outline=color, width=resistor_outline_width)
    else:
        points = [(-resistor_length/2, -resistor_width/2),
                  (-resistor_length/2, +resistor_width/2),
                  (+resistor_length/2, +resistor_width/2),
                  (+resistor_length/2, -resistor_width/2),
                  (-resistor_length/2, -resistor_width/2),
                  (-resistor_length/2, +resistor_width/2)]
        points = [(c_x(x_center + p[0]*math.cos(angle)-p[1]*math.sin(angle)),
                   c_y(y_center + p[0]*math.sin(angle)+p[1]*math.cos(angle))) for p in points]
        draw.line(points, width=resistor_outline_width, fill=color, joint='curve')


def draw_wire(draw, xy, color=(0, 0, 0)):
    if not xy:
        return

    xy_new = xy
    if not isinstance(xy_new[0], tuple):
        xy_new = [(xy[i], xy[i+1]) for i in range(0, len(xy), 2)]
    xy_new = [(c_x(elem[0]), c_y(elem[1])) for elem in xy_new]

    draw.line(xy_new, width=wire_outline_width, fill=color, joint='curve')


def draw_contact(draw, x_center, y_center, color=(0, 0, 0)):
    draw.ellipse(
        [c_x(x_center - contact_size / 2), c_y(y_center - contact_size / 2),
         c_x(x_center + contact_size / 2), c_y(y_center + contact_size / 2)],
        fill=(255, 255, 255), outline=color, width=resistor_outline_width)
    draw.line([c_x(x_center - contact_size / 2), c_y(y_center + contact_size / 2),
               c_x(x_center + contact_size / 2), c_y(y_center - contact_size / 2)],
              width=wire_outline_width, fill=color)


def create_frame_stage_1(step, max_steps):
    img = create_empty_frame()
    draw = ImageDraw.Draw(img)

    draw_resistor(draw, 0, 0)
    draw_resistor(draw, -900, 0)
    draw_resistor(draw, +900, 0)

    draw_wire(draw, [+250, 0, +650, 0])
    draw_wire(draw, [-250, 0, -650, 0])
    draw_wire(draw, [-450, 0, -450, +900, +1350, +900, +1350, 0, +1150, 0])
    draw_wire(draw, [+450, 0, +450, -900, -1350, -900, -1350, 0, -1150, 0])

    turn_step = int(max_steps * 18.0 / 31.0)
    if step <= turn_step:
        draw_wire(draw, [+1550, +1100 * step / turn_step, +1350, +900 * step / turn_step])
        draw_wire(draw, [-1550, -1100 * step / turn_step, -1350, -900 * step / turn_step])
        draw_contact(draw, +1550, +1100 * step / turn_step)
        draw_contact(draw, -1550, -1100 * step / turn_step)
    else:
        draw_wire(draw, [+1550 - 1550 * (step-turn_step) / (max_steps - 1 - turn_step), +1150,
                         +1350 - 1350 * (step-turn_step) / (max_steps - 1 - turn_step), +900])
        draw_wire(draw, [-1550 + 1550 * (step-turn_step) / (max_steps - 1 - turn_step), -1150,
                         -1350 + 1350 * (step-turn_step) / (max_steps - 1 - turn_step), -900])
        draw_contact(draw, +1550 - 1550 * (step-turn_step) / (max_steps - 1 - turn_step), +1150)
        draw_contact(draw, -1550 + 1550 * (step-turn_step) / (max_steps - 1 - turn_step), -1150)

    return img


def create_frame_stage_2(step, max_steps):
    img = create_empty_frame()
    draw = ImageDraw.Draw(img)

    draw_resistor(draw, 0, 0)

    draw_wire(draw, [+250, 0, +450, 0])
    draw_wire(draw, [-250, 0, -450, 0])
    draw_wire(draw, [-450, 0, -450, +900, 0, +900])
    draw_wire(draw, [+450, 0, +450, -900, 0, -900])
    draw_wire(draw, [0, +1150, 0, +900])
    draw_wire(draw, [0, -1150, 0, -900])

    draw_contact(draw, 0, +1150)
    draw_contact(draw, 0, -1150)

    turn_step = int(max_steps * 2.0 / 3.0)
    if step <= turn_step:
        phi = math.atan2(step, turn_step)
        draw_wire(draw, [+450, 0, +900 - resistor_length / 2 * math.cos(phi),
                         +450 * math.tan(phi) - resistor_length / 2 * math.sin(phi)])
        draw_wire(draw, [-450, 0, -900 + resistor_length / 2 * math.cos(phi),
                         -450 * math.tan(phi) + resistor_length / 2 * math.sin(phi)])
        draw_wire(draw, [0, +900, +1350, +900, +1350, +900 * math.tan(phi),
                         +900 + resistor_length / 2 * math.cos(phi),
                         +450 * math.tan(phi) + resistor_length / 2 * math.sin(phi)])
        draw_wire(draw, [0, -900, -1350, -900, -1350, -900 * math.tan(phi),
                         -900 - resistor_length / 2 * math.cos(phi),
                         -450 * math.tan(phi) - resistor_length / 2 * math.sin(phi)])
        draw_resistor(draw, +900, +450 * math.tan(phi), angle=phi)
        draw_resistor(draw, -900, -450 * math.tan(phi), angle=phi)
    else:
        phi = math.atan2(max_steps - 1 - step, max_steps - 1 - turn_step)
        draw_wire(draw, [+450, 0, +900 - 450 * math.sin(phi), 0,
                         +900 - resistor_length / 2 * math.sin(phi), +450 - resistor_length / 2 * math.cos(phi)])
        draw_wire(draw, [-450, 0, -900 + 450 * math.sin(phi), 0,
                         -900 + resistor_length / 2 * math.sin(phi), -450 + resistor_length / 2 * math.cos(phi)])
        draw_wire(draw, [0, +900, +900 + 450 * math.tan(phi), +900,
                         +900 + resistor_length / 2 * math.sin(phi), +450 + resistor_length / 2 * math.cos(phi)])
        draw_wire(draw, [0, -900, -900 - 450 * math.tan(phi), -900,
                         -900 - resistor_length / 2 * math.sin(phi), -450 - resistor_length / 2 * math.cos(phi)])
        draw_resistor(draw, +900, +450, angle=math.pi / 2 - phi)
        draw_resistor(draw, -900, -450, angle=math.pi / 2 - phi)

    return img


def create_frame_stage_3(step, max_steps):
    img = create_empty_frame()
    draw = ImageDraw.Draw(img)

    draw_resistor(draw, 0, 0)
    draw_resistor(draw, +900, +450, angle=math.pi / 2)
    draw_resistor(draw, -900, -450, angle=math.pi / 2)

    draw_wire(draw, [+250, 0, +900, 0, +900, +200])
    draw_wire(draw, [-250, 0, -900, 0, -900, -200])
    draw_wire(draw, [0, +1150, 0, +900])
    draw_wire(draw, [0, -1150, 0, -900])
    draw_wire(draw, [0, +900, +900, +900, +900, +700])
    draw_wire(draw, [0, -900, -900, -900, -900, -700])

    draw_contact(draw, 0, +1150)
    draw_contact(draw, 0, -1150)

    draw_wire(draw, [-450 - 450 * step / (max_steps - 1), 0, -450 - 450 * step / (max_steps - 1), +900, 0, +900])
    draw_wire(draw, [+450 + 450 * step / (max_steps - 1), 0, +450 + 450 * step / (max_steps - 1), -900, 0, -900])

    return img


def create_frame_stage_4(step, max_steps):
    img = create_empty_frame()
    draw = ImageDraw.Draw(img)

    draw_resistor(draw, +900, +450, angle=math.pi / 2)
    draw_resistor(draw, -900, -450, angle=math.pi / 2)

    draw_wire(draw, [0, +1150, 0, +900])
    draw_wire(draw, [0, -1150, 0, -900])
    draw_wire(draw, [0, +900, +900, +900, +900, +700])
    draw_wire(draw, [0, -900, -900, -900, -900, -700])
    draw_wire(draw, [-900, -200, -900, +900, 0, +900])
    draw_wire(draw, [+900, +200, +900, -900, 0, -900])

    draw_contact(draw, 0, +1150)
    draw_contact(draw, 0, -1150)

    turn_step = int(max_steps * 0.5)
    if step <= turn_step:
        phi = -math.atan2(900 * step / turn_step, 900)
        draw_resistor(draw, 0, 0, angle=phi)
        draw_wire(draw, [+resistor_length / 2 * math.cos(phi), +resistor_length / 2 * math.sin(phi),
                         +900, +900 * math.tan(phi)])
        draw_wire(draw, [-resistor_length / 2 * math.cos(phi), -resistor_length / 2 * math.sin(phi),
                         -900, -900 * math.tan(phi)])
    else:
        phi = math.atan2(max_steps - 1 - step, max_steps - 1 - turn_step)
        draw_resistor(draw, 0, 0, angle=phi - math.pi / 2)
        draw_wire(draw, [+resistor_length / 2 * math.sin(phi), -resistor_length / 2 * math.cos(phi),
                         +900 * math.tan(phi), -900])
        draw_wire(draw, [-resistor_length / 2 * math.sin(phi), +resistor_length / 2 * math.cos(phi),
                         -900 * math.tan(phi), +900])

    return img


def create_frame_stage_5(step, max_step):
    img = create_empty_frame()
    draw = ImageDraw.Draw(img)

    draw_resistor(draw, 0, 0, angle=math.pi / 2)

    draw_wire(draw, [0, +1150, 0, +resistor_length / 2])
    draw_wire(draw, [0, -1150, 0, -resistor_length / 2])

    draw_contact(draw, 0, +1150)
    draw_contact(draw, 0, -1150)

    draw_resistor(draw, +900, +450 - 450 * step / (max_step - 1), angle=math.pi / 2)
    draw_resistor(draw, -900, -450 + 450 * step / (max_step - 1), angle=math.pi / 2)

    draw_wire(draw, [0, +900, +900, +900, +900, +700 - (700 - resistor_length / 2) * step / (max_step - 1)])
    draw_wire(draw, [0, -900, -900, -900, -900, -700 + (700 - resistor_length / 2) * step / (max_step - 1)])
    draw_wire(draw, [-900, -200 + (200 + resistor_length / 2) * step / (max_step - 1), -900, +900, 0, +900])
    draw_wire(draw, [+900, +200 - (200 + resistor_length / 2) * step / (max_step - 1), +900, -900, 0, -900])

    return img


if __name__ == '__main__':
    frames = []
    for n_frame in range(30):
        frames.append(create_frame_stage_1(n_frame, 30))
    for n_frame in range(30):
        frames.append(create_frame_stage_2(n_frame, 30))
    for n_frame in range(15):
        frames.append(create_frame_stage_3(n_frame, 15))
    for n_frame in range(30):
        frames.append(create_frame_stage_4(n_frame, 30))
    for n_frame in range(10):
        frames.append(create_frame_stage_5(n_frame, 10))

    # frames = [frame.resize((image_width, image_height), resample=Image.LANCZOS) for frame in frames]
    frames[0].save('scheme_transformation.gif', format='GIF', append_images=frames[1:], save_all=True,
                   duration=20, loop=1)
