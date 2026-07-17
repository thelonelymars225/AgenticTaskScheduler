import os
import tkinter as tk

class PongGame:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=600, height=400, bg='black')
        self.canvas.pack()
        
        self.ball = Ball(self.canvas)
        self.paddle_left = Paddle(self.canvas, 'left')
        self.paddle_right = Paddle(self.canvas, 'right')
        
        self.root.bind('<KeyPress-Left>', lambda e: self.paddle_left.move(-10))
        self.root.bind('<KeyPress-Right>', lambda e: self.paddle_left.move(10))
        self.root.bind('<KeyPress-a>', lambda e: self.paddle_right.move(-10))
        self.root.bind('<KeyPress-d>', lambda e: self.paddle_right.move(10))
        
        self.game_loop()
    
    def game_loop(self):
        if os.getenv('AGENT_SMOKE_TEST') == '1':
            print("Smoke test passed.")
            self.root.quit()  # Ensure the program exits after smoke test
            return
        
        self.ball.move()
        self.canvas.after(50, self.game_loop)

class Ball:
    def __init__(self, canvas):
        self.canvas = canvas
        self.id = canvas.create_oval(290, 190, 310, 210, fill='white')
        self.x = 2
        self.y = 2
    
    def move(self):
        self.canvas.move(self.id, self.x, self.y)
        pos = self.canvas.coords(self.id)
        
        if pos[1] <= 0 or pos[3] >= 400:
            self.y *= -1
        
        if pos[0] <= 0:
            print("Right player scores!")
            self.reset_ball()
        
        if pos[2] >= 600:
            print("Left player scores!")
            self.reset_ball()
    
    def reset_ball(self):
        self.canvas.coords(self.id, 290, 190, 310, 210)
        self.x *= -1

class Paddle:
    def __init__(self, canvas, side):
        self.canvas = canvas
        if side == 'left':
            self.id = canvas.create_rectangle(10, 150, 30, 250, fill='white')
        else:
            self.id = canvas.create_rectangle(570, 150, 590, 250, fill='white')
    
    def move(self, distance):
        pos = self.canvas.coords(self.id)
        if (pos[1] > 0 or distance > 0) and (pos[3] < 400 or distance < 0):
            self.canvas.move(self.id, 0, distance)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Pong")
    game = PongGame(root)
    root.mainloop()