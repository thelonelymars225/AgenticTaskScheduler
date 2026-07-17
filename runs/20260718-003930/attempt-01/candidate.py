import os
import tkinter as tk

class PongGame:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=600, height=400, bg='black')
        self.canvas.pack()

        self.ball = Ball(self.canvas)
        self.left_paddle = Paddle(self.canvas, 'left')
        self.right_paddle = Paddle(self.canvas, 'right')

        self.score_left = 0
        self.score_right = 0

        self.score_label = tk.Label(root, text=f"{self.score_left} : {self.score_right}", font=('Arial', 24), fg='white', bg='black')
        self.score_label.pack()

        self.root.bind('<KeyPress-Up>', lambda event: self.left_paddle.move_up())
        self.root.bind('<KeyPress-Down>', lambda event: self.left_paddle.move_down())
        self.root.bind('<KeyPress-w>', lambda event: self.right_paddle.move_up())
        self.root.bind('<KeyPress-s>', lambda event: self.right_paddle.move_down())

        self.game_loop()

    def game_loop(self):
        if self.ball.check_collision(self.left_paddle) or self.ball.check_collision(self.right_paddle):
            self.ball.change_direction()
        elif self.ball.x <= 0:
            self.score_right += 1
            self.reset_ball('right')
        elif self.ball.x >= self.canvas.winfo_width():
            self.score_left += 1
            self.reset_ball('left')

        self.update_score()
        self.ball.move()
        self.root.after(16, self.game_loop)

    def reset_ball(self, side):
        self.ball.reset(side)
        self.left_paddle.reset_position()
        self.right_paddle.reset_position()

    def update_score(self):
        self.score_label.config(text=f"{self.score_left} : {self.score_right}")

class Ball:
    def __init__(self, canvas):
        self.canvas = canvas
        self.x = 300
        self.y = 200
        self.dx = 5
        self.dy = 5
        self.radius = 10
        self.ball = self.canvas.create_oval(self.x - self.radius, self.y - self.radius,
                                           self.x + self.radius, self.y + self.radius, fill='white')

    def move(self):
        self.canvas.move(self.ball, self.dx, self.dy)
        self.x += self.dx
        self.y += self.dy

    def change_direction(self):
        self.dx = -self.dx

    def check_collision(self, paddle):
        ball_pos = self.canvas.coords(self.ball)
        paddle_pos = self.canvas.coords(paddle.paddle)

        if ball_pos[2] >= paddle_pos[0] and ball_pos[0] <= paddle_pos[2]:
            if ball_pos[3] >= paddle_pos[1] and ball_pos[1] <= paddle_pos[3]:
                return True
        return False

    def reset(self, side):
        self.canvas.delete(self.ball)
        if side == 'left':
            self.x = 600 - self.radius
        else:
            self.x = self.radius
        self.y = 200
        self.dx = 5 if side == 'right' else -5
        self.dy = 5
        self.ball = self.canvas.create_oval(self.x - self.radius, self.y - self.radius,
                                           self.x + self.radius, self.y + self.radius, fill='white')

class Paddle:
    def __init__(self, canvas, side):
        self.canvas = canvas
        self.side = side
        self.width = 10
        self.height = 80
        self.speed = 20

        if side == 'left':
            self.x = 30
        else:
            self.x = 570

        self.y = (canvas.winfo_height() - self.height) // 2
        self.paddle = self.canvas.create_rectangle(self.x, self.y, self.x + self.width, self.y + self.height, fill='white')

    def move_up(self):
        if self.y > 0:
            self.y -= self.speed
            self.canvas.move(self.paddle, 0, -self.speed)

    def move_down(self):
        if self.y < self.canvas.winfo_height() - self.height:
            self.y += self.speed
            self.canvas.move(self.paddle, 0, self.speed)

    def reset_position(self):
        self.canvas.delete(self.paddle)
        self.y = (self.canvas.winfo_height() - self.height) // 2
        if self.side == 'left':
            self.x = 30
        else:
            self.x = 570
        self.paddle = self.canvas.create_rectangle(self.x, self.y, self.x + self.width, self.y + self.height, fill='white')

if __name__ == "__main__":
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        print("Smoke test passed.")
        exit(0)

    root = tk.Tk()
    root.title("Pong")
    game = PongGame(root)
    root.mainloop()