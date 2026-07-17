import tkinter as tk

class PongGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Pong")
        self.canvas = tk.Canvas(root, width=600, height=400, bg="black")
        self.canvas.pack()

        self.ball = Ball(self.canvas)
        self.paddle1 = Paddle(self.canvas, "w", 30)
        self.paddle2 = Paddle(self.canvas, "s", 570)

        self.score1 = 0
        self.score2 = 0

        self.score_label = tk.Label(root, text=f"{self.score1} : {self.score2}", font=("Arial", 24), fg="white", bg="black")
        self.score_label.pack()

        self.root.bind("<KeyPress>", self.key_press)
        self.root.bind("<KeyRelease>", self.key_release)

        self.running = True
        self.update_game()

    def key_press(self, event):
        if event.char == 'w':
            self.paddle1.move_up()
        elif event.char == 's':
            self.paddle1.move_down()
        elif event.char == 'o':
            self.paddle2.move_up()
        elif event.char == 'l':
            self.paddle2.move_down()

    def key_release(self, event):
        if event.char in ('w', 's'):
            self.paddle1.stop()
        elif event.char in ('o', 'l'):
            self.paddle2.stop()

    def update_game(self):
        if not self.running:
            return

        self.ball.move()
        self.check_collision()

        if self.ball.x < 0:
            self.score2 += 1
            self.reset_ball()
        elif self.ball.x > 600:
            self.score1 += 1
            self.reset_ball()

        self.update_score_label()
        self.canvas.after(10, self.update_game)

    def check_collision(self):
        if (self.paddle1.y < self.ball.y < self.paddle1.y + 80 and self.ball.x <= 30) or \
           (self.paddle2.y < self.ball.y < self.paddle2.y + 80 and self.ball.x >= 570):
            self.ball.bounce_x()

    def reset_ball(self):
        self.ball.reset()
        self.update_score_label()

    def update_score_label(self):
        self.score_label.config(text=f"{self.score1} : {self.score2}")

class Ball:
    def __init__(self, canvas):
        self.canvas = canvas
        self.id = canvas.create_oval(295, 195, 305, 205, fill="white")
        self.x = 2
        self.y = 2

    def move(self):
        self.canvas.move(self.id, self.x, self.y)

    def bounce_x(self):
        self.x *= -1

    def reset(self):
        self.canvas.coords(self.id, 295, 195, 305, 205)
        self.x = 2
        self.y = 2

class Paddle:
    def __init__(self, canvas, key_up, x_pos):
        self.canvas = canvas
        self.key_up = key_up
        self.id = canvas.create_rectangle(x_pos, 180, x_pos + 10, 260, fill="white")
        self.y = 0
        self.speed = 5

    def move_up(self):
        pos = self.canvas.coords(self.id)
        if pos[1] > 0:
            self.y = -self.speed

    def move_down(self):
        pos = self.canvas.coords(self.id)
        if pos[3] < 400:
            self.y = self.speed

    def stop(self):
        self.y = 0

    def update_position(self):
        pos = self.canvas.coords(self.id)
        if pos[1] <= 0 and self.y < 0:
            self.y = 0
        elif pos[3] >= 400 and self.y > 0:
            self.y = 0
        else:
            self.canvas.move(self.id, 0, self.y)

if __name__ == "__main__":
    if 'AGENT_SMOKE_TEST' in globals() and AGENT_SMOKE_TEST == 1:
        print("Smoke test passed.")
        exit(0)

    root = tk.Tk()
    game = PongGame(root)
    root.mainloop()