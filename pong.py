from graphics import *
import time
import random
import math
import sys

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
PADDLE_MARGIN = 25
PADDLE_SPEED = 10
INITIAL_BALL_VELOCITY_X = 10

class Game:
    def __init__(self, window):
        self._window = window

        self._window.set_background_color(Color(0, 0, 0))

        self._left_score = 0
        # self._left_score_label = Text(Point(WINDOW_WIDTH / 3, PADDLE_MARGIN), "0")
        # self._left_score_label.setFill('white')
        # self._left_score_label.setSize(30)
        # self._left_score_label.draw(self._window)

        self._right_score = 0
        # self._right_score_label = Text(Point(2 * WINDOW_WIDTH / 3, PADDLE_MARGIN), "0")
        # self._right_score_label.setFill('white')
        # self._right_score_label.setSize(30)
        # self._right_score_label.draw(self._window)

        self._ball = Ball()
        self._ball.set_velocity_x(INITIAL_BALL_VELOCITY_X)
        self._ball.draw(window)

        self._paddle_left = Paddle(PADDLE_MARGIN)
        self._paddle_left.draw(window)

        self._paddle_right = Paddle(WINDOW_WIDTH - PADDLE_MARGIN)
        self._paddle_right.draw(window)

    def handle_input(self):
        pass
        if self._window.is_key_pressed('q'):
             sys.exit(0)

        if self._window.is_key_pressed('w') and self._paddle_left.can_go_up():
            self._paddle_left.set_velocity(-PADDLE_SPEED)
        elif self._window.is_key_pressed('s') and self._paddle_left.can_go_down():
            self._paddle_left.set_velocity(PADDLE_SPEED)
        else:
            self._paddle_left.set_velocity(0)

        if self._window.is_key_pressed('Up') and self._paddle_right.can_go_up():
            self._paddle_right.set_velocity(-PADDLE_SPEED)
        elif self._window.is_key_pressed('Down') and self._paddle_right.can_go_down():
            self._paddle_right.set_velocity(PADDLE_SPEED)
        else:
            self._paddle_right.set_velocity(0)

    def step(self):
        """
        Updates all game state before rendering the next frame.
        """
        self._ball.step()
        self._paddle_left.step()
        self._paddle_right.step()

        # Hitting on left.
        if self._ball.intersects(self._paddle_left.get_bounds()):
            if self._paddle_left.get_velocity() != 0:
                self._ball.set_velocity_y(self._paddle_left.get_velocity())
            self._ball.bounce_x()

        # Hitting on right.
        if self._ball.intersects(self._paddle_right.get_bounds()):
            if self._paddle_right.get_velocity() != 0:
                self._ball.set_velocity_y(self._paddle_right.get_velocity())
            self._ball.bounce_x()

        # Ball going off top.
        if self._ball.get_bounds().top_y() < 0:
            self._ball.bounce_y()

        # Ball going off bottom.
        if self._ball.get_bounds().bottom_y() > WINDOW_HEIGHT:
            self._ball.bounce_y()

        # Ball going off left.
        if self._ball.get_bounds().right_x() < 0:
            self._ball.place_at(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
            self._ball.set_velocity_x(INITIAL_BALL_VELOCITY_X)
            self._ball.set_velocity_y(0)
            self._right_score += 1
            self._right_score_label.setText(str(self._right_score))

        # Ball going off right.
        if self._ball.get_bounds().left_x() > WINDOW_WIDTH:
            self._ball.place_at(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
            self._ball.set_velocity_x(-INITIAL_BALL_VELOCITY_X)
            self._ball.set_velocity_y(0)
            self._left_score += 1
            self._left_score_label.setText(str(self._left_score))

class Ball:
    WIDTH = 20

    def __init__(self):
        self._square = Rectangle(0, 0, Ball.WIDTH, Ball.WIDTH)
        self._square.center_at(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        self._square.set_color(Color.WHITE)

        self._velx = 0
        self._vely = 0

    def place_at(self, x, y):
        self._square.center_at(x, y)

    def get_bounds(self):
        return self._square.clone()

    def set_velocity_x(self, velocity):
        self._velx = velocity

    def set_velocity_y(self, velocity):
        self._vely = velocity

    def bounce_x(self):
        self._velx *= -1

    def bounce_y(self):
        self._vely *= -1

    def step(self):
        self._square.translate(self._velx, self._vely)

    def intersects(self, rect):
        if self._square.bottom_y() < rect.top_y():
            return False
        if self._square.top_y() > rect.bottom_y():
            return False
        if self._square.right_x() < rect.left_x():
            return False
        if self._square.left_x() > rect.right_x():
            return False
        return True

    def draw(self, window):
        window.add(self._square)

class Paddle:
    PADDLE_HEIGHT = 100
    PADDLE_WIDTH = 20

    def __init__(self, x_position):
        self._rect = Rectangle(0, 0, Paddle.PADDLE_WIDTH, Paddle.PADDLE_HEIGHT)
        self._rect.center_at(x_position, WINDOW_HEIGHT // 2)

        self._rect.set_color(Color.WHITE)
        self._velocity = 0

    def get_bounds(self):
        return self._rect.clone()

    def set_velocity(self, velocity):
        self._velocity = velocity

    def get_velocity(self):
        return self._velocity

    def can_go_up(self):
        return self._rect.top_y() > 0

    def can_go_down(self):
        return self._rect.bottom_y() < WINDOW_HEIGHT

    def step(self):
        self._rect.translate(0, self._velocity)

    def draw(self, window):
        window.add(self._rect)

def main():
    window = Window("Pong", WINDOW_WIDTH, WINDOW_HEIGHT)
    game = Game(window)

    def update(window):
        game.handle_input()
        game.step()

    window.show(tick=update)

main()
