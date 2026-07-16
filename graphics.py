from abc import abstractmethod
import ctypes
import math
import sdl3
import time

class GraphicsError(Exception):
    """An exception type for graphics errors."""
    pass

# Map string key ids to SLD3 scancodes. We could do much of this by
# computing the offsets from scancode A, although this would not be
# robust to (albiet unlikely) changes in the SDL3 scancode
# definitions.
_scancodes = {
  'a': sdl3.SDL_SCANCODE_A,
  'b': sdl3.SDL_SCANCODE_B,
  'c': sdl3.SDL_SCANCODE_C,
  'd': sdl3.SDL_SCANCODE_D,
  'e': sdl3.SDL_SCANCODE_E,
  'f': sdl3.SDL_SCANCODE_F,
  'g': sdl3.SDL_SCANCODE_G,
  'h': sdl3.SDL_SCANCODE_H,
  'i': sdl3.SDL_SCANCODE_I,
  'j': sdl3.SDL_SCANCODE_J,
  'k': sdl3.SDL_SCANCODE_K,
  'l': sdl3.SDL_SCANCODE_L,
  'm': sdl3.SDL_SCANCODE_M,
  'n': sdl3.SDL_SCANCODE_N,
  'o': sdl3.SDL_SCANCODE_O,
  'p': sdl3.SDL_SCANCODE_P,
  'q': sdl3.SDL_SCANCODE_Q,
  'r': sdl3.SDL_SCANCODE_R,
  's': sdl3.SDL_SCANCODE_S,
  't': sdl3.SDL_SCANCODE_T,
  'u': sdl3.SDL_SCANCODE_U,
  'v': sdl3.SDL_SCANCODE_V,
  'w': sdl3.SDL_SCANCODE_W,
  'x': sdl3.SDL_SCANCODE_X,
  'y': sdl3.SDL_SCANCODE_Y,
  'z': sdl3.SDL_SCANCODE_Z,
  'Up': sdl3.SDL_SCANCODE_UP,
  'Down': sdl3.SDL_SCANCODE_DOWN,
  'Left': sdl3.SDL_SCANCODE_LEFT,
  'Right': sdl3.SDL_SCANCODE_RIGHT,
}

# Map from font IDs to possible system locations for the font's TTF
# file. This could obviously fail depending on system, and for now the
# most reliable way to get a font is to include the TTF file in the
# project directory. (See also _open_font defined below.)
_font_locations = {
  'arial': ['C:\\Windows\\Fonts\\arial.ttf',
            '/Library/Fonts/Arial.ttf',
            '/Library/Fonts/Arial Unicode.ttf']
}

def _open_font(text_engine, font_name, font_size):
    """
    Attempts to open a TTF font, returning and SDL font object for
    that font at the given size. Searches for a TTF file in the following
    order:

      1. A file called 'font_name' in the current directory.
      2. A file called 'font_name.ttf' in the current directory.
      3. A system font file in the order specified by _font_locations.

    If no suitable font file can be found, raises a GraphicsError.
    """
    search_paths = [font_name, f'{font_name}.ttf']
    search_paths.extend(_font_locations[font_name])

    font = None
    for font_path in search_paths:
        font = sdl3.TTF_OpenFont(font_path.encode('utf-8'), font_size)
        if font:
            break
    if not font:
        raise GraphicsError(f'Could not find a font path for: {font_id}')
    return font


class TextureRender:
    """Abstract class for objects which render themselves using SDL
    textures."""

    def __init__(self):
        self._texture = None

    @abstractmethod
    def _make_texture(self, renderer):
        """Create and return a texture object."""

    @abstractmethod
    def _get_bounds(self):
        """Return the current render boundary as an SDL FRect."""

    def _render(self, renderer):
        if not self._texture:
            self._texture = self._make_texture(renderer)
            if not self._texture:
                raise GraphicsError(f"{sdl3.SDL_GetError().decode()}")
        bounds = self._get_bounds()
        sdl3.SDL_RenderTexture(renderer, self._texture, None, bounds)


class Positioned:
    """Abstract class for objects which have an (x, y) position."""

    def __init__(self, x=0, y=0):
        self._x_position = x
        self._y_position = y

    def get_x(self):
        return self._x_position

    def get_y(self):
        return self._y_position

    def set_x(self, x):
        self._x_position = x

    def set_y(self, y):
        self._y_position = y

    def translate(self, dx, dy):
        self._x_position += dx
        self._y_position += dy


class Bounded(Positioned):
    """Abstract class for objects which have a width / height bound."""

    def __init__(self, x, y, width, height):
        Positioned.__init__(self, x, y)
        self._width = width
        self._height = height

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height

    def get_center(self):
        center_x = (self.get_x() + self._width) / 2
        center_y = (self.get_y() + self._height) / 2
        return Point(center_x, center_y)

    def set_center(self, center_x, center_y):
        self.set_x(center_x - self.get_width() / 2)
        self.set_y(center_y - self.get_height() / 2)

    def _bounds_as_frect(self):
        return sdl3.SDL_FRect(
            self.get_x(),
            self.get_y(),
            self._width,
            self._height)

    def set_width(self, width):
        self._width = width

    def set_height(self, height):
        self._height = height

    def scale(self, scale):
        self._width *= scale
        self._height *= scale


class Window:
    """A class representing an application window."""

    def __init__(self, title='Window', width=800, height=600):
        if not sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO):
            raise GraphicsError(f"SDL Init Failed: {sdl3.SDL_GetError().decode()}")

        if not sdl3.TTF_Init():
            print(f"TTF Init Error: {sdl3.SDL_GetError().decode()}")
            sdl3.SDL_Quit()
            raise GraphicsError("TTF initialization failed")

        self._background_color = Color(0, 0, 0)
        self._is_open = True
        self._children = []
        self._text_children = []
        self._tick = 1/60
        self._event = sdl3.SDL_Event()

        window_flags = sdl3.SDL_WINDOW_OPENGL
        window = sdl3.SDL_CreateWindow(title.encode('utf-8'), width, height, window_flags)
        if not window:
            sdl3.SDL_Quit()
            raise GraphicsError(f"Failed to create window: {sdl3.SDL_GetError().decode()}")
        self._window = window

        num_keys = ctypes.c_int(0)
        keystate = sdl3.SDL_GetKeyboardState(ctypes.byref(num_keys))
        self._keyboard = ctypes.cast(keystate, ctypes.POINTER(ctypes.c_bool * 512)).contents

        renderer = sdl3.SDL_CreateRenderer(window, None)
        if not renderer:
            sdl3.SDL_DestroyWindow(window)
            sdl3.SDL_Quit()
            raise GraphicsError(f"Failed to create renderer: {sdl3.SDL_GetError().decode()}")
        sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
        self._renderer = renderer
        self._text_engine = sdl3.TTF_CreateRendererTextEngine(self._renderer)

    def update(self):
        """Renders a single frame to the window."""
        while sdl3.SDL_PollEvent(ctypes.byref(self._event)):
            if self._event.type == sdl3.SDL_EVENT_QUIT:
                self.close()
                sdl3.SDL_Quit() # TODO: Handle multiple open windows.
                return

        self._background_color.setr_draw_color(self._renderer)
        sdl3.SDL_RenderClear(self._renderer)
        for tchild in self._text_children:
            tchild._prepare_text(self._text_engine)
        for child in self._children:
            child._render(self._renderer)
        sdl3.SDL_RenderPresent(self._renderer)

    def set_background_color(self, color):
        self._background_color = color

    def add(self, child):
        self._children.append(child)
        if callable(getattr(child, '_prepare_text', None)):
            self._text_children.append(child)

    def is_open(self):
        return self._is_open

    def show(self, tick=None):
        while self.is_open():
            if tick:
                tick(self)
            self.update()
            time.sleep(self._tick)

    def is_key_pressed(self, key):
        return self._keyboard[_scancodes[key]]

    def close(self):
        self._is_open = False
        sdl3.SDL_DestroyRenderer(self._renderer)
        sdl3.SDL_DestroyWindow(self._window)


class Color:
    """Represents an RGBA color."""
    def __init__(self, red, green, blue, alpha=255):
        self._r = red
        self._g = green
        self._b = blue
        self._alpha = alpha

    def as_fcolor(self):
        return sdl3.SDL_FColor(self._r / 255, self._g / 255, self._b / 255, self._alpha / 255)

    def setr_draw_color(self, renderer):
        sdl3.SDL_SetRenderDrawColor(renderer, self._r, self._g, self._b, self._alpha)

    def clone(self):
        return Color(self._r, self._g, self._b, self._alpha)


# Some predefined colors.
Color.BLACK = Color(0, 0, 0)
Color.BLUE = Color(0, 0, 255)
Color.BROWN = Color(165, 42, 42)
Color.CYAN = Color(0, 255, 255)
Color.GRAY = Color(128, 128, 128)
Color.GREEN = Color(0, 128, 0)
Color.LIME = Color(0, 255, 0)
Color.MAGENTA = Color(255, 0, 255)
Color.MAROON = Color(128, 0, 0)
Color.NAVY = Color(0, 0, 128)
Color.OLIVE = Color(128, 128, 0)
Color.ORANGE = Color(255, 165, 0)
Color.PINK = Color(255, 192, 203)
Color.PURPLE = Color(128, 0, 128)
Color.RED = Color(255, 0, 0)
Color.SILVER = Color(192, 192, 192)
Color.TEAL = Color(0, 128, 128)
Color.WHITE = Color(255, 255, 255)
Color.YELLOW = Color(255, 255, 0)


class Point(Positioned):
    """A single (x,y) point."""

    def __init__(self, x, y):
        Positioned.__init__(self)


class Circle(TextureRender, Positioned):
    """Renders a circle."""

    def __init__(self, center_x, center_y, radius):
        Positioned.__init__(self, center_x, center_y)
        TextureRender.__init__(self)
        self._radius = radius

        # Expanded radius with an anti-aliasing border.
        self._extended_radius = self._radius + 1
        self._extended_diameter = 2 * self._extended_radius

        self.set_color(Color.WHITE)

    def set_color(self, color):
        self._color = color
        if self._texture:
            sdl3.SDL_SetTextureColorMod(self._texture, color._r, color._g, color._b)
            sdl3.SDL_SetTextureAlphaMod(self._texture, color._alpha)
        else:
            self._render_pixels()

    def _make_texture(self, renderer):
        """To avoid the per-frame cost of calculating circle
        rendering, including anti-aliasing, Circles are rendered to a
        static texture that can be re-used on each frame. This method
        creates (or re-creates) that texture.
        """
        texture = sdl3.SDL_CreateTexture(
            renderer,
            sdl3.SDL_PIXELFORMAT_RGBA32,
            sdl3.SDL_TEXTUREACCESS_STATIC,
            self._extended_diameter,
            self._extended_diameter)
        sdl3.SDL_UpdateTexture(texture, None, self._pixels, self._extended_diameter * 4)
        sdl3.SDL_SetTextureBlendMode(texture, sdl3.SDL_BLENDMODE_BLEND)
        return texture

    def _get_bounds(self):
        return sdl3.SDL_FRect(
            self.get_x() - self._extended_radius,
            self.get_y() - self._extended_radius,
            float(self._extended_diameter),
            float(self._extended_diameter))


    def _render_pixels(self):
        """Render the Circle to a byte array of pixel values."""
        pixels_size = (self._extended_diameter + 1) * (self._extended_diameter + 1) * 4
        pixels = bytearray(pixels_size)
        for y in range(self._extended_diameter + 1):
            dy = self._extended_radius - y
            for x in range(self._extended_diameter + 1):
                dx = self._extended_radius - x
                dist = math.sqrt(dx * dx + dy * dy)

                if dist >= self._radius + 0.5:
                    alpha = 0
                elif dist <= self._radius - 0.5:
                    alpha = 255
                else:
                    alpha = int(255 * (self._radius + 0.5 - dist))

                alpha = max(0, min(255, alpha))

                offset = (y * self._extended_diameter + x) * 4
                pixels[offset] = self._color._r
                pixels[offset + 1] = self._color._g
                pixels[offset + 2] = self._color._b
                pixels[offset + 3] = alpha
        self._pixels = bytes(pixels)


class Triangle(Bounded):
    """Renders a triangle."""

    def __init__(self, x1, y1, x2, y2, x3, y3):
        left = min(x1, x2, x3)
        top = min(y1, y2, y3)
        width = max(x1, x2, x3) - left
        height = max(y1, y2, y3) - top
        Bounded.__init__(self, left, top, width, height)
        self._x1 = x1
        self._y1 = y1
        self._x2 = x2
        self._y2 = y2
        self._x3 = x3
        self._y3 = y3
        self.set_color(Color.WHITE)

    def set_color(self, color):
        self._color = color

    def _render(self, renderer):
        color = self._color.as_fcolor()

        vertices = [
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self._x1, self._y1),
                color,
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self._x2, self._y2),
                color,
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self._x3, self._y3),
                color,
                sdl3.SDL_FPoint(0.0, 0.0))]

        indices = [0, 1, 2]

        # Covert to C arrays.
        num_vertices = len(vertices)
        vert_array = (sdl3.SDL_Vertex * num_vertices)(*vertices)
        idx_array = (ctypes.c_int * len(indices))(*indices)

        # Render as a mesh.
        sdl3.SDL_RenderGeometry(
            renderer,
            None,
            vert_array,
            len(vertices),
            idx_array,
            len(indices))


class Rectangle(Bounded):
    """Renders a rectangle."""

    def __init__(self, left_x, top_y, width, height):
        Bounded.__init__(self, left_x, top_y, width, height)
        self._color = Color.WHITE

    def set_color(self, color):
        self._color = color

    def left_x(self):
        return self.get_x()

    def top_y(self):
        return self.get_y()

    def right_x(self):
        return self.get_x() + self.get_width()

    def bottom_y(self):
        return self.get_y() + self.get_height()

    def clone(self):
        copy = Rectangle(self.left_x(), self.top_y(),
                         self.get_width(), self.get_height())
        copy.set_color(self._color.clone())
        return copy

    def _render(self, renderer):
        """Draw the rectangle using the given renderer."""
        color = self._color.as_fcolor()
        vertices = [
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self.left_x(), self.top_y()),
                color,
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self.right_x(), self.top_y()),
                color,
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self.right_x(), self.bottom_y()),
                color,
                sdl3.SDL_FPoint(0.0, 0.0)),
            sdl3.SDL_Vertex(
                sdl3.SDL_FPoint(self.left_x(), self.bottom_y()),
                color,
                sdl3.SDL_FPoint(0.0, 0.0))]

        indices = [0, 1, 2, 0, 2, 3]

        # Covert to C arrays.
        num_vertices = len(vertices)
        vert_array = (sdl3.SDL_Vertex * num_vertices)(*vertices)
        idx_array = (ctypes.c_int * len(indices))(*indices)

        # Render as a 2-triangle mesh.
        sdl3.SDL_RenderGeometry(
            renderer,
            None,
            vert_array,
            len(vertices),
            idx_array,
            len(indices))


class TextArea(Positioned):
    """Renders text for display on a Window."""

    def __init__(self, text='', x=0, y=0, font='arial', font_size=24):
        Positioned.__init__(self, x, y)
        self._text = text.encode('utf-8')
        self._sdl_text = None
        self._font = font
        self._font_size = font_size
        self._sdl_font = None
        self.set_color(Color.WHITE)

    def set_text(self, text):
        self._text = text
        if self._sdl_text:
            sdl3.TTF_SetTextString(self._sdl_text, self._text.encode('utf-8'), len(text))

    def set_color(self, color):
        self._color = color
        if self._sdl_text:
            sdl3.TTF_SetTextColor(self._sdl_text, color._r, color._g, color._b, color._alpha)

    def set_font(self, font):
        self._font = font

    def set_font_size(self, font_size):
        self._font_size = font_size

    def _prepare_text(self, text_engine):
        if not self._sdl_text:
            font = _open_font(text_engine, self._font, self._font_size)
            self._sdl_text = sdl3.TTF_CreateText(text_engine, font, self._text, 0)
            self.set_color(self._color)

    def _render(self, renderer):
        if self._sdl_text:
            sdl3.TTF_DrawRendererText(self._sdl_text, self.get_x(), self.get_y())
        else:
            self._color.setr_draw_color(renderer)
            sdl3.SDL_RenderDebugText(renderer, self.get_x(), self.get_y(), self._text)

    def _destroy(self):
        if self._sdl_text:
            sdl3.TTF_DestroyText(self._sdl_text)


class Image(Bounded, TextureRender):
    """Renders an image from file."""

    def __init__(self, image_path, x=0, y=0):
        Bounded.__init__(self, x, y, 0, 0)
        TextureRender.__init__(self)
        self._image_path = image_path.encode('utf-8')

    def _make_texture(self, renderer):
        texture = sdl3.SDL_image.IMG_LoadTexture(renderer, self._image_path)
        if not texture:
            raise GraphicsError(f"{sdl3.SDL_GetError().decode()}")
        props = sdl3.SDL_GetTextureProperties(texture)
        self.set_width(sdl3.SDL_GetNumberProperty(props, b"SDL.texture.width", 0))
        self.set_height(sdl3.SDL_GetNumberProperty(props, b"SDL.texture.height", 0))
        return texture

    def _get_bounds(self):
        return self._bounds_as_frect()
