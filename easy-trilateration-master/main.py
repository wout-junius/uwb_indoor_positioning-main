import argparse
from easy_trilateration.least_squares import *
from easy_trilateration.graph import *
import turtle
from random import randrange

meter2pixel = 100

def trilateration_example():
    arr = [Circle(0  * meter2pixel, 0  * meter2pixel, .5 * meter2pixel),
           Circle(   * meter2pixel, 0  * meter2pixel, .5 * meter2pixel),
           Circle(0  * meter2pixel, 5  * meter2pixel, .5 * meter2pixel),
           Circle(.5 * meter2pixel, 1  * meter2pixel, .5 * meter2pixel)]
    result, meta = easy_least_squares(arr)
    create_circle(result, target=True)
    draw(arr)


# def history_example():
#     arr = Trilateration([Circle(100, 100, 70.71),
#                          Circle(100, 50, 50),
#                          Circle(50, 50, 0),
#                          Circle(50, 100, 50)])

#     arr2 = Trilateration([Circle(100, 100, 50),
#                           Circle(100, 50, 70.71),
#                           Circle(50, 50, 50),
#                           Circle(50, 100, 0)])

#     arr3 = Trilateration([Circle(100, 100, 0),
#                           Circle(100, 50, 50),
#                           Circle(50, 50, 70.71),
#                           Circle(50, 100, 50)])

#     arr4 = Trilateration([Circle(100, 100, 50),
#                           Circle(100, 50, 0),
#                           Circle(50, 50, 50),
#                           Circle(50, 100, 70.71)])

#     hist = [arr, arr2, arr3, arr4, arr]

#     solve_history(hist)

#     return _a


def screen_init(width=1200, height=800, t=turtle):
    t.setup(width, height)
    t.tracer(False)
    t.hideturtle()
    t.speed(0)

def turtle_init(t=turtle):
    t.hideturtle()
    t.speed(0)


def draw_line(x0, y0, x1, y1, color="black", t=turtle):
    t.pencolor(color)

    t.up()
    t.goto(x0, y0)
    t.down()
    t.goto(x1, y1)
    t.up()


def draw_fastU(x, y, length, color="black", t=turtle):
    draw_line(x, y, x, y + length, color, t)


def draw_fastV(x, y, length, color="black", t=turtle):
    draw_line(x, y, x + length, y, color, t)


def draw_cycle(x, y, r, color="black", t=turtle):
    t.hideturtle()
    t.speed(0)
    t.pencolor(color)
    t.up()
    t.goto(x, y - r)
    t.setheading(0)
    t.down()
    t.circle(r)
    t.up()


def fill_cycle(x, y, r, color="black", t=turtle):
    t.up()
    t.goto(x, y)
    t.down()
    t.dot(r, color)
    t.up()


def write_txt(x, y, txt, color="black", t=turtle, f=('Arial', 12, 'normal')):

    t.pencolor(color)
    t.up()
    t.goto(x, y)
    t.down()
    t.write(txt, move=False, align='left', font=f)
    t.up()


def draw_rect(x, y, w, h, color="black", t=turtle):
    t.pencolor(color)

    t.up()
    t.goto(x, y)
    t.down()
    t.goto(x + w, y)
    t.goto(x + w, y + h)
    t.goto(x, y + h)
    t.goto(x, y)
    t.up()


def fill_rect(x, y, w, h, color=("black", "black"), t=turtle):
    t.begin_fill()
    draw_rect(x, y, w, h, color, t)
    t.end_fill()
    pass


def clean(t=turtle):
    t.clear()


def draw_ui(t):
    write_txt(-200, -200, "UWB Positon", "black",  t, f=('Arial', 20, 'normal'))
    fill_rect(-800, -50, 1600, 10, "black", t)
    write_txt(0, -100, "WALL", "black",  t, f=('Arial', 12, 'normal'))


def draw_uwb_anchor(x, y, txt, t):
    r = 20
    fill_cycle(x, y, r, "red", t)
    write_txt(x, y, txt + ": " + "M",
              "black",  t, f=('Arial', 8, 'normal'))

def draw_uwb_radius(x, y, txt, range, t):
    # write_txt(x + r, y, txt + ": " + str(range) + "M",
    #           "black",  t, f=('Arial', 8, 'normal'))
    clean(t)
    draw_cycle(int(x),int(y),range,"black",t)

def draw_uwb_tag(x, y, txt, range, t):
    r = 20
    clean(t)
    fill_cycle(x, y, r, "green", t)
    write_txt(x + r, y, txt + ": " + str(range) + "M",
              "black",  t, f=('Arial', 8, 'normal'))
    draw_cycle(int(x),int(y),range,"black",t)

# def draw_uwb_tag(x, y, txt, t):
    # pos_x = -250 + int(x * meter2pixel)
    # pos_y = 150 - int(y * meter2pixel)
    # r = 20
    # fill_cycle(pos_x, pos_y, r, "blue", t)
    # write_txt(pos_x, pos_y, txt + ": (" + str(x) + "," + str(y) + ")",
    #           "black",  t, f=('Arial', 16, 'normal'))


def correct_measurement(x):
    return (x - 2) * 100

if __name__ == '__main__':

    t_ui = turtle.Turtle()
    t_a1 = turtle.Turtle()
    t_a2 = turtle.Turtle()
    t_a3 = turtle.Turtle()
    t_ra1 = turtle.Turtle()
    t_ra2 = turtle.Turtle()
    t_ra3 = turtle.Turtle()
    t_t1 = turtle.Turtle()

    turtle_init(t_ui)
    turtle_init(t_a1)
    turtle_init(t_a2)
    turtle_init(t_a3)
    turtle_init(t_ra1)
    turtle_init(t_ra2)
    turtle_init(t_ra3)
    turtle_init(t_t1)

    draw_ui(t_ui)
    
    arr_val = [[0, 0],
                [500, 0],
                [500, 450]]

    draw_uwb_anchor(arr_val[0][0], arr_val[0][1], "A:L-BOT", t_a1)
    draw_uwb_anchor(arr_val[1][0], arr_val[1][1], "A:R-BOT", t_a2)
    draw_uwb_anchor(arr_val[2][0], arr_val[2][1], "A:R-UP", t_a3)

    while True:
        ra1 = 300+ randrange(100)
        ra2 = 300+ randrange(100)
        ra3 = 300+ randrange(100)
        # create_circle(result, target=True)
            # draw(arr)
        
        draw_uwb_radius(arr_val[0][0], arr_val[0][1], "A:L-BOT", ra1, t_ra1)
        draw_uwb_radius(arr_val[1][0], arr_val[1][1], "A:R-BOT", ra1, t_ra2)
        draw_uwb_radius(arr_val[2][0], arr_val[2][1], "A:R-UP", ra1, t_ra3)

        arr = [Circle(arr_val[0][0], arr_val[0][1], ra1),
               Circle(arr_val[1][0], arr_val[1][1], ra2),
               Circle(arr_val[2][0], arr_val[2][1], ra3)]
        # clean(t_t1)
        result, meta = easy_least_squares(arr)
        print(result.center.x, result.center.y, result.radius)
        draw_uwb_tag(result.center.x, result.center.y, "TAG", int(result.radius), t_t1)

    # parser = argparse.ArgumentParser(
    #     description='Trilateration solver and 2D grapher')
    # parser.add_argument('--file', nargs='?', help='data filename', default='resources/capture_combined.csv')

    # args = parser.parse_args()

    # _filename = args.file

    # file = pd.read_csv(_filename)

    # temp_tril = []
    # history = []
    # millis = file['millis'][0]

    # node = dict()

    # # draws = []
    # #  for value in node.values():
    # #      draws.append(create_point(value))
    # #  draw(draws)
    # enabled_nodes = [3, 1, 6]
    # actual = []
    # for _, row in file.iterrows():
    #     actual.append(Point(float(row['target_x']), float(row['target_y'])))
    #     if enabled_nodes.__contains__(row['node']) or False:
    #         if millis == row['millis']:
    #             temp_tril.append(Circle(float(row['x']), float(row['y']), rssi_to_distance(row['rssi'])))
    #         else:
    #             history.append(Trilateration(temp_tril.copy()))
    #             temp_tril = []
    #             millis = row['millis']

    # #  solve_history_linear(history)
    # #  _a = static(history, actual)
    # solve_history(history)
    # _b = static(history, actual)
