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

    def _render(self, renderer):

        radius = self._radius
        cx = self._center._x
        cy = self._center._y

        for y in range(-radius, radius + 1):
            x_exact = math.sqrt(radius * radius - y * y)

            x_int = int(x_exact)
            frac = x_exact - x_int

            # Fully covered interior span
            self._fill_color.setr_draw_color(renderer)
            sdl3.SDL_RenderLine(
                renderer,
                float(cx - x_int),
                float(cy + y),
                float(cx + x_int),
                float(cy + y),
            )

            # Anti-aliased edge pixels
            edge_alpha = int(frac * self._fill_color._alpha)

            if edge_alpha > 0:
                sdl3.SDL_SetRenderDrawColor(
                    renderer,
                    self._fill_color._r, self._fill_color._g, self._fill_color._b, edge_alpha
                )

                sdl3.SDL_RenderPoint(
                    renderer,
                    float(cx - x_int - 1),
                    float(cy + y)
                )

                sdl3.SDL_RenderPoint(
                    renderer,
                    float(cx + x_int + 1),
                    float(cy + y)
                )

    def _render_outline(self, renderer):

        def plot(x, y, alpha):
            alpha = max(0, min(255, int(self._fill_color._alpha * 255)))

            self._fill_color.setr_draw_color(renderer)
            sdl3.SDL_SetRenderDrawColor(renderer, self._fill_color._r, self._fill_color._g, self._fill_color._b, alpha)
            sdl3.SDL_RenderPoint(renderer, float(x), float(y))

        cx = self._center._x
        cy = self._center._y

        for x in range(self._radius + 1):
            y = math.sqrt(self._radius * self._radius - x * x)

            yi = int(y)
            frac = y - yi

            # Upper octants
            plot(cx + x, cy + yi, 1.0 - frac)
            plot(cx + x, cy + yi + 1, frac)

            plot(cx - x, cy + yi, 1.0 - frac)
            plot(cx - x, cy + yi + 1, frac)

            plot(cx + x, cy - yi, 1.0 - frac)
            plot(cx + x, cy - yi - 1, frac)

            plot(cx - x, cy - yi, 1.0 - frac)
            plot(cx - x, cy - yi - 1, frac)

            # Swap x/y for remaining octants
            plot(cx + yi, cy + x, 1.0 - frac)
            plot(cx + yi + 1, cy + x, frac)

            plot(cx - yi, cy + x, 1.0 - frac)
            plot(cx - yi - 1, cy + x, frac)

            plot(cx + yi, cy - x, 1.0 - frac)
            plot(cx + yi + 1, cy - x, frac)

            plot(cx - yi, cy - x, 1.0 - frac)
            plot(cx - yi - 1, cy - x, frac)

    def _render_surface(self, renderer):
        """
        Generates a localized surface, applies distance field anti-aliasing,
        and uploads to the renderer.
        """
        diameter = int(self._radius * 2) + 2
        surface = sdl3.SDL_CreateSurface(diameter, diameter, sdl3.SDL_PIXELFORMAT_RGBA32)
        sdl3.SDL_SetSurfaceBlendMode(surface, sdl3.SDL_BLENDMODE_BLEND)

        # Get direct pointer access to pixels
        pixel_data = ctypes.cast(surface.contents.pixels, ctypes.POINTER(ctypes.c_uint8))
        pitch = surface.contents.pitch
        center = self._radius + 1

        for y in range(diameter):
            for x in range(diameter):
                # Calculate distance from pixel center to circle center
                dx = x - self._center._x + 0.5
                dy = y - self._center._y + 0.5
                distance = math.sqrt(dx*dx + dy*dy)

                # Distance field antialiasing math
                if distance < self._radius - 0.5:
                    alpha = 255
                elif distance > self._radius + 0.5:
                    alpha = 0
                else:
                    # Smoothstep / Linear blending region
                    alpha = int(255 * ((self._radius + 0.5) - distance))

                if alpha > 0:
                    offset = (y * pitch) + (x * 4)
                    pixel_data[offset] = 255
                    pixel_data[offset+1] = 0
                    pixel_data[offset+2] = 0
                    pixel_data[offset+3] = alpha

        # Convert finalized surface to a texture for high-performance rendering
        texture = sdl3.SDL_CreateTextureFromSurface(renderer, surface)
        sdl3.SDL_DestroySurface(surface)

        # Render immediately
        dest_rect = sdl3.SDL_FRect(self._center._x - center,
                                   self._center._y - center,
                                   diameter,
                                   diameter)
        sdl3.SDL_RenderTexture(renderer, texture, None, dest_rect)
        sdl3.SDL_DestroyTexture(texture)

    def _render_triange_fan(self, renderer, num_segments=64):
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

        num_vertices = len(border_vertices)
        border_vert_array = (sdl3.SDL_Vertex * num_vertices)(*border_vertices)
        fill_vert_array = (sdl3.SDL_Vertex * num_vertices)(*fill_vertices)
        idx_array = (ctypes.c_int * len(indices))(*indices)

        sdl3.SDL_RenderGeometry(
            renderer,
            None,
            border_vert_array,
            len(border_vertices),
            idx_array,
            len(indices))
        sdl3.SDL_RenderGeometry(
            renderer,
            None,
            fill_vert_array,
            len(fill_vertices),
            idx_array,
            len(indices))

    def _render_rough(self, renderer):
        """Midpoint circle algorithm."""
        x = self._radius - 1
        y = 0
        tx = 1
        ty = 1
        error = tx - (self._radius * 2)
        border_points = []

        self._fill_color.setr_draw_color(renderer)

        while x >= y:
            border_points.extend([
                sdl3.SDL_FPoint(self._center._x + x, self._center._y - y),
                sdl3.SDL_FPoint(self._center._x + x, self._center._y + y),
                sdl3.SDL_FPoint(self._center._x - x, self._center._y - y),
                sdl3.SDL_FPoint(self._center._x - x, self._center._y + y),
                sdl3.SDL_FPoint(self._center._x + y, self._center._y - x),
                sdl3.SDL_FPoint(self._center._x + y, self._center._y + x),
                sdl3.SDL_FPoint(self._center._x - y, self._center._y - x),
                sdl3.SDL_FPoint(self._center._x - y, self._center._y + x)])

            sdl3.SDL_RenderLine(renderer,
                                float(self._center._x - x),
                                float(self._center._y - y),
                                float(self._center._x + x),
                                float(self._center._y - y))
            sdl3.SDL_RenderLine(renderer,
                                float(self._center._x - x),
                                float(self._center._y + y),
                                float(self._center._x + x),
                                float(self._center._y + y))
            sdl3.SDL_RenderLine(renderer,
                                float(self._center._x - y),
                                float(self._center._y - x),
                                float(self._center._x + y),
                                float(self._center._y - x))
            sdl3.SDL_RenderLine(renderer,
                                float(self._center._x - y),
                                float(self._center._y + x),
                                float(self._center._x + y),
                                float(self._center._y + x))

            if error <= 0:
                y += 1
                error += ty
                ty += 2

            if error > 0:
                x -= 1
                tx += 2
                error += tx - (self._radius * 2)

        self._border_color.setr_draw_color(renderer)
        num_points = len(border_points)
        CArrayType = sdl3.SDL_FPoint * num_points
        c_points = CArrayType(*border_points)
        sdl3.SDL_RenderPoints(renderer, c_points, num_points)

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
