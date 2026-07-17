"""Pong — hand-written baseline for comparison with AI-generated version."""
import tkinter as tk
import random

W, H = 800, 500
PAD_W, PAD_H = 12, 80
BALL_R = 10
PAD_SPEED = 20
BALL_SPEED = 6

class Paddle:
    def __init__(self, canvas: tk.Canvas, x: int, color: str):
        self.canvas = canvas
        self.x = x
        self.y = H // 2 - PAD_H // 2
        self.color = color
        self.rect = canvas.create_rectangle(x, self.y, x + PAD_W, self.y + PAD_H, fill=color)

    def move_up(self):
        if self.y > 0:
            self.y -= PAD_SPEED
            self.canvas.move(self.rect, 0, -PAD_SPEED)

    def move_down(self):
        if self.y < H - PAD_H:
            self.y += PAD_SPEED
            self.canvas.move(self.rect, 0, PAD_SPEED)


class Ball:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.x = W // 2
        self.y = H // 2
        self.vx = BALL_SPEED * random.choice([-1, 1])
        self.vy = BALL_SPEED * random.uniform(-1, 1)
        self.oval = canvas.create_oval(
            self.x - BALL_R, self.y - BALL_R,
            self.x + BALL_R, self.y + BALL_R, fill="white"
        )

    def move(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        # Bounce off top/bottom
        if self.y - BALL_R <= 0 or self.y + BALL_R >= H:
            self.vy = -self.vy
        self.canvas.move(self.oval, self.vx, self.vy)
        # Score check
        if self.x - BALL_R <= 0:
            return True  # right player scores
        if self.x + BALL_R >= W:
            return False  # left player scores
        return None

    def hit_paddle(self, px: int, py: int) -> bool:
        if px <= self.x <= px + PAD_W and py <= self.y <= py + PAD_H:
            self.vx = -self.vx
            self.x += self.vx  # nudge out of paddle
            return True
        return False


class PongGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pong")
        self.canvas = tk.Canvas(self.root, width=W, height=H, bg="black")
        self.canvas.pack()

        self.p1 = Paddle(self.canvas, 20, "white")        # left
        self.p2 = Paddle(self.canvas, W - 20 - PAD_W, "white")  # right
        self.ball = Ball(self.canvas)

        self.p1_score = 0
        self.p2_score = 0
        self.score_text = self.canvas.create_text(
            W // 2, 30, text="0 - 0", fill="white", font=("Arial", 24)
        )

        self.root.bind("w", lambda _: self.p1.move_up())
        self.root.bind("s", lambda _: self.p1.move_down())
        self.root.bind("<Up>", lambda _: self.p2.move_up())
        self.root.bind("<Down>", lambda _: self.p2.move_down())

        self.update()

    def update(self):
        result = self.ball.move()
        if result is not None:
            if result:  # right scores
                self.p2_score += 1
            else:  # left scores
                self.p1_score += 1
            self.canvas.itemconfig(self.score_text, text=f"{self.p1_score} - {self.p2_score}")
            self.ball = Ball(self.canvas)

        self.ball.hit_paddle(self.p1.x, self.p1.y)
        self.ball.hit_paddle(self.p2.x, self.p2.y)

        self.root.after(16, self.update)  # ~60 FPS

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    PongGame().run()
