from PIL import Image, ImageDraw


image_width = 330
image_height = 140
resistor_length = 50
resistor_width = 20
resistor_outline_width = 3


def c_x(x):
    return x + image_width/2


def c_y(y):
    return y + image_height/2


def create_frame_stage_1(step, maxsteps):
    img = Image.new('RGB', (image_width, image_height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([c_x(-resistor_length/2), c_y(-resistor_width/2), c_x(resistor_length/2), c_y(resistor_width/2)],
                   outline=(0, 0, 0), width=resistor_outline_width)

    return img


if __name__ == '__main__':
    frames = []
    frames.append(create_frame_stage_1(0, 0))
    frames[0].save('scheme_transformation.gif', format='GIF', append_images=frames[1:], save_all=True, duration=100, loop=1)
