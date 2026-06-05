import ctypes
import math
import sdl3
import sys
import time

class GraphicsException(Exception):
    pass

class Window:
    def __init__(self, title='Window', width=800, height=600):
        self._background_color = Color(0, 0, 0)
        self._is_open = True
        self._children = []
        self._tick = 1/60
        self._event = sdl3.SDL_Event()

        if not sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO):
            raise Exception(f"SDL Init Failed: {sdl3.SDL_GetError().decode()}")

        window_flags = sdl3.SDL_WINDOW_OPENGL
        window = sdl3.SDL_CreateWindow(title.encode('utf-8'), width, height, window_flags)
        if not window:
            sdl3.SDL_Quit()
            raise GraphicsException(f"Failed to create window: {sdl3.SDL_GetError().decode()}")
        self._window = window

        renderer = sdl3.SDL_CreateRenderer(window, None)
        if not renderer:
            sdl3.SDL_DestroyWindow(window)
            sdl3.SDL_Quit()
            raise GraphicsException(f"Failed to create renderer: {sdl3.SDL_GetError().decode()}")
        sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
        self._renderer = renderer

    def update(self):
        while sdl3.SDL_PollEvent(ctypes.byref(self._event)):
            if self._event.type == sdl3.SDL_EVENT_QUIT:
                self.close()
                sdl3.SDL_Quit() # TODO: Handle multiple open windows.
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
        self._color = Color(255, 255, 255)
        self._texture = None

        # Expanded radius with an anti-aliasing border.
        self._extended_radius = int(self._radius + 1.0)
        self._extended_diameter = 2 * self._extended_radius

    def set_color(self, color):
        self._color = color

    def _make_texture(self, renderer):
        texture = sdl3.SDL_CreateTexture(
                    renderer,
                    sdl3.SDL_PIXELFORMAT_RGBA8888,
                    sdl3.SDL_TEXTUREACCESS_TARGET,
                    self._extended_diameter,
                    self._extended_diameter)
        sdl3.SDL_SetTextureScaleMode(texture, sdl3.SDL_SCALEMODE_LINEAR)
        sdl3.SDL_SetTextureBlendMode(texture, sdl3.SDL_BLENDMODE_BLEND)

        prev_target = sdl3.SDL_GetRenderTarget(renderer)
        sdl3.SDL_SetRenderTarget(renderer, texture)

        self._render_direct(renderer, self._extended_radius, self._extended_radius)

        sdl3.SDL_SetRenderTarget(renderer, prev_target)
        self._texture = texture

    def _render_direct(self, renderer, center_x, center_y):
        left_edge = center_x - self._extended_radius
        top_edge = center_y - self._extended_radius

        for y_offset in range(self._extended_diameter + 1):
            y = top_edge + y_offset
            dy = center_y - y
            for x_offset in range(self._extended_diameter + 1):
                x = left_edge + x_offset
                dx = center_x - x
                dist = math.sqrt(dx * dx + dy * dy)

                if dist >= self._radius + 0.5:
                    continue
                elif dist <= self._radius - 0.5:
                    alpha = 255
                else:
                    alpha = int(255 * (self._radius + 0.5 - dist))

                alpha = max(0, min(255, alpha))

                sdl3.SDL_SetRenderDrawColor(renderer,
                                            self._color._r,
                                            self._color._g,
                                            self._color._b,
                                            alpha)
                sdl3.SDL_RenderPoint(renderer, x, y)

    def _render(self, renderer):
        #self._render_direct(renderer, self._center._x, self._center._y)
        #return
        if not self._texture:
            self._make_texture(renderer)
        bounds = sdl3.SDL_FRect(
            self._center._x - self._extended_radius,
            self._center._y - self._extended_radius,
            self._extended_diameter+1,
            self._extended_diameter+1)
        sdl3.SDL_RenderTexture(renderer, self._texture, None, bounds)


class Rectangle:
    def __init__(self, left_x, top_y, width, height):
        self._left_x = left_x
        self._top_y = top_y
        self._right_x = left_x + width
        self._bottom_y = top_y + height
        self._width = width
        self._height = height
        self._color = Color(255, 255, 255)

    def set_color(self, color):
        self._color = color

    def _render(self, renderer):
        color = self._color.as_fcolor()
        vertices = [
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self._left_x, self._top_y),
                color,
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self._right_x, self._top_y),
                color,
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self._right_x, self._bottom_y),
                color,
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self._left_x, self._bottom_y),
                color,
                sdl3.SDL_FPoint(0.0, 0.0))]

        indices = [0, 1, 2, 0, 2, 3]

        # Covert to C arrays.
        num_vertices = len(vertices)
        vert_array = (sdl3.SDL_Vertex * num_vertices)(*vertices)
        idx_array = (ctypes.c_int * len(indices))(*indices)

        # Render.
        sdl3.SDL_RenderGeometry(
            renderer,
            None,
            vert_array,
            len(vertices),
            idx_array,
            len(indices))


def main():
    window = Window('Test Window', 800, 600)
    window.set_background_color(Color(30, 100, 200))

    circle = Circle(Point(400, 300), 300)
    circle.set_color(Color(0, 80, 0))
    window.add(circle)

    circle2 = Circle(Point(400, 300), 95)
    circle2.set_color(Color(0, 200, 0))
    window.add(circle2)

    rectangle = Rectangle(200, 100, 300, 150)
    rectangle.set_color(Color(50, 50, 200))
    #window.add(rectangle)

    window.show()
    return 0

if __name__ == "__main__":
    sys.exit(main())
