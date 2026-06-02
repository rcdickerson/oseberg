import ctypes
import math
import sdl3
import sys
import time

if not sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO):
    raise Exception(f"SDL Init Failed: {sdl3.SDL_GetError().decode()}")

sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_MULTISAMPLEBUFFERS, 1)
sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_MULTISAMPLESAMPLES, 4)

class GraphicsException(Exception):
    pass

class Window:
    def __init__(self, title='Window', width=800, height=600):
        self._background_color = Color(0, 0, 0)
        self._is_open = True
        self._children = []
        self._tick = 1/60
        self._event = sdl3.SDL_Event()

        flags = sdl3.SDL_WINDOW_RESIZABLE
        window = sdl3.SDL_CreateWindow(title.encode('utf-8'), width, height, flags)
        if not window:
            sdl3.SDL_Quit()
            raise GraphicsException(f"Failed to create window: {sdl3.SDL_GetError().decode()}")
        self._window = window

        renderer = sdl3.SDL_CreateRenderer(window, None)
        if not renderer:
            sdl3.SDL_DestroyWindow(window)
            sdl3.SDL_Quit()
            raise GraphicsException(f"Failed to create renderer: {sdl3.SDL_GetError().decode()}")
        self._renderer = renderer

    def update(self):
        while sdl3.SDL_PollEvent(ctypes.byref(self._event)):
            if self._event.type == sdl3.SDL_EVENT_QUIT:
                self.close()
                sdl3.SDL_Quit()
                return

        self._background_color.setr_draw_color(self._renderer)
        sdl3.SDL_RenderClear(self._renderer)
        for child in self._children:
            child._render(self._renderer)
        sdl3.SDL_RenderPresent(self._renderer)

    def set_background_color(self, color):
        self._background_color = color

    def add(self, child):
        self._children.append(child)

    def is_open(self):
        return self._is_open

    def show(self):
        while self.is_open():
            self.update()
            time.sleep(self._tick)

    def close(self):
        self._is_open = False
        sdl3.SDL_DestroyRenderer(self._renderer)
        sdl3.SDL_DestroyWindow(self._window)


class Color:
    def __init__(self, red, green, blue, alpha=255):
        self._r = red
        self._g = green
        self._b = blue
        self._alpha = alpha

    def as_fcolor(self):
        return sdl3.SDL_FColor(self._r / 255, self._g / 255, self._b / 255, self._alpha / 255)

    def setr_draw_color(self, renderer):
        sdl3.SDL_SetRenderDrawColor(renderer, self._r, self._g, self._b, self._alpha)


class Point:
    def __init__(self, x, y):
        self._x = x
        self._y = y


class Circle:
    def __init__(self, center, radius):
        self._center = center
        self._radius = radius
        self._border_width = 1
        self._border_color = Color(255, 255, 255)
        self._fill_color = Color(255, 255, 255)

    def set_border_width(self, width):
        self._border_width = width

    def set_border_color(self, color):
        self._border_color = color

    def set_fill_color(self, color):
        self._fill_color = color

    def _render(self, renderer, num_segments=64):
        """Render smoothly using a triangle fan."""

        center_vertex = sdl3.SDL_Vertex(
            sdl3.SDL_FPoint(self._center._x, self._center._y),
            self._fill_color.as_fcolor(),
            sdl3.SDL_FPoint(0.0, 0.0))

        fill_vertices = [center_vertex]
        border_vertices = [center_vertex]

        for i in range(num_segments):
            angle = 2.0 * math.pi * i / num_segments

            border_x = self._center._x + (self._radius * math.cos(angle))
            border_y = self._center._y + (self._radius * math.sin(angle))

            fill_x = self._center._x + ((self._radius - self._border_width) * math.cos(angle))
            fill_y = self._center._y + ((self._radius - self._border_width) * math.sin(angle))

            border_vertices.append(sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(border_x, border_y),
                self._border_color.as_fcolor(),
                sdl3.SDL_FPoint(0.0, 0.0)))

            fill_vertices.append(sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(fill_x, fill_y),
                self._fill_color.as_fcolor(),
                sdl3.SDL_FPoint(0.0, 0.0)))

        indices = []
        for i in range(1, num_segments):
            indices.extend([0, i, i + 1])
        indices.extend([0, num_segments, 1])

        # Covert to C arrays.
        num_vertices = len(border_vertices)
        border_vert_array = (sdl3.SDL_Vertex * num_vertices)(*border_vertices)
        fill_vert_array = (sdl3.SDL_Vertex * num_vertices)(*fill_vertices)
        idx_array = (ctypes.c_int * len(indices))(*indices)

        # Render border.
        sdl3.SDL_RenderGeometry(
            renderer,
            None,
            border_vert_array,
            len(border_vertices),
            idx_array,
            len(indices))

        # Render fill.
        sdl3.SDL_RenderGeometry(
            renderer,
            None,
            fill_vert_array,
            len(fill_vertices),
            idx_array,
            len(indices))


class Rectangle:
    def __init__(self, left_x, top_y, width, height):
        self._left_x = left_x
        self._top_y = top_y
        self._right_x = left_x + width
        self._bottom_y = top_y + height
        self._width = width
        self._height = height
        self._border_width = 1
        self._border_color = Color(255, 255, 255)
        self._fill_color = Color(255, 255, 255)

    def set_border_width(self, width):
        self._border_width = width

    def set_border_color(self, color):
        self._border_color = color

    def set_fill_color(self, color):
        self._fill_color = color

    def _render(self, renderer):
        border_vertices = [
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self._left_x, self._top_y),
                self._border_color.as_fcolor(),
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self._right_x, self._top_y),
                self._border_color.as_fcolor(),
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self._right_x, self._bottom_y),
                self._border_color.as_fcolor(),
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self._left_x, self._bottom_y),
                self._border_color.as_fcolor(),
                sdl3.SDL_FPoint(0.0, 0.0))]

        fill_left_x = self._left_x + self._border_width
        fill_right_x = self._right_x - self._border_width
        fill_top_y = self._top_y + self._border_width
        fill_bottom_y = self._bottom_y - self._border_width
        fill_vertices = [
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(fill_left_x, fill_top_y),
                self._fill_color.as_fcolor(),
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(fill_right_x, fill_top_y),
                self._fill_color.as_fcolor(),
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(fill_right_x, fill_bottom_y),
                self._fill_color.as_fcolor(),
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(fill_left_x, fill_bottom_y),
                self._fill_color.as_fcolor(),
                sdl3.SDL_FPoint(0.0, 0.0))]

        indices = [0, 1, 2, 0, 2, 3]

        # Covert to C arrays.
        num_vertices = len(border_vertices)
        border_vert_array = (sdl3.SDL_Vertex * num_vertices)(*border_vertices)
        fill_vert_array = (sdl3.SDL_Vertex * num_vertices)(*fill_vertices)
        idx_array = (ctypes.c_int * len(indices))(*indices)

        # Render border.
        sdl3.SDL_RenderGeometry(
            renderer,
            None,
            border_vert_array,
            len(border_vertices),
            idx_array,
            len(indices))

        # Render fill.
        sdl3.SDL_RenderGeometry(
            renderer,
            None,
            fill_vert_array,
            len(fill_vertices),
            idx_array,
            len(indices))


def main():
    window = Window('Test Window', 800, 600)
    window.set_background_color(Color(30, 100, 200))

    circle = Circle(Point(400, 300), 100)
    circle.set_fill_color(Color(50, 180, 20))
    circle.set_border_color(Color(0, 80, 0))
    circle.set_border_width(5)
    window.add(circle)

    rectangle = Rectangle(200, 100, 300, 150)
    rectangle.set_fill_color(Color(50, 50, 200))
    window.add(rectangle)

    window.show()
    return 0

if __name__ == "__main__":
    sys.exit(main())
