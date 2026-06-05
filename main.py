from graphics import *
import sys

def main():
    window = Window('Test Window', 800, 600)
    window.set_background_color(Color(30, 100, 200))

    circle = Circle(Point(400, 300), 100)
    circle.set_color(Color(0, 80, 0))
    window.add(circle)

    circle2 = Circle(Point(400, 300), 95)
    circle2.set_color(Color(0, 200, 0))
    window.add(circle2)

    rectangle1 = Rectangle(190, 90, 320, 170)
    rectangle1.set_color(Color(255, 255, 255))
    window.add(rectangle1)

    rectangle2 = Rectangle(200, 100, 300, 150)
    rectangle2.set_color(Color(50, 50, 200))
    window.add(rectangle2)

    text = TextArea('Test Text', 50, 50)
    text.set_color(Color.GREEN)
    window.add(text)

    def update(window):
        circle.translate(1, 0)
        circle2.translate(1, 0)

    window.show(tick=update)
    return 0

if __name__ == "__main__":
    sys.exit(main())
