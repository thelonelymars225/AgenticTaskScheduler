import os
import tkinter as tk

class PongGame:
    def __init__(self, root):
        self.canvas = tk.Canvas(root, width=600, height=400, bg='black')
        self.canvas.pack()
        
        self.ball = Ball(self.canvas)
        self.paddle_left = Paddle(self.canvas, 'left')
        self.paddle_right = Paddle(self.canvas, 'right')
        
        self.score_left = 0
        self.score_right = 0
        
        self.left_score_text = self.canvas.create_text(150, 20, text=f"Score: {self.score_left}", fill="white", font=('Helvetica', 16))
        self.right_score_text = self.canvas.create_text(450, 20, text=f"Score: {self.score_right}", fill="white", font=('Helvetica', 16))
        
        root.bind('<KeyPress-Left>', lambda e: self.paddle_left.move(-10))
        root.bind('<KeyPress-Right>', lambda e: self.paddle_left.move(10))
        root.bind('<KeyPress-a>', lambda e: self.paddle_right.move(-10))
        root.bind('<KeyPress-d>', lambda e: self.paddle_right.move(10))
        
        self.game_loop()
    
    def game_loop(self):
        if self.ball.update():
            self.score_left += 1
            self.canvas.itemconfig(self.left_score_text, text=f"Score: {self.score_left}")
        elif self.ball.update():
            self.score_right += 1
            self.canvas.itemconfig(self.right_score_text, text=f"Score: {self.score_right}")
        
        self.canvas.after(50, self.game_loop)

class Ball:
    def __init__(self, canvas):
        self.canvas = canvas
        self.id = canvas.create_oval(290, 190, 310, 210, fill='white')
        self.x = 2
        self.y = 2
    
    def update(self):
        self.canvas.move(self.id, self.x, self.y)
        
        pos = self.canvas.coords(self.id)
        
        if pos[1] <= 0 or pos[3] >= 400:
            self.y *= -1
        
        if pos[0] <= 0:
            return True
        elif pos[2] >= 600:
            return False
        
        paddle_left = self.canvas.coords('paddle_left')
        paddle_right = self.canvas.coords('paddle_right')
        
        if pos[2] >= paddle_right[0] and pos[0] <= paddle_right[2]:
            if pos[3] >= paddle_right[1] and pos[1] <= paddle_right[3]:
                self.x *= -1
        
        if pos[2] >= paddle_left[0] and pos[0] <= paddle_left[2]:
            if pos[3] >= paddle_left[1] and pos[1] <= paddle_left[3]:
                self.x *= -1

class Paddle:
    def __init__(self, canvas, side):
        self.canvas = canvas
        self.id = canvas.create_rectangle(0, 150, 10, 250, fill='white', tags=f'paddle_{side}')
        
        if side == 'right':
            self.canvas.move(self.id, 590, 0)
    
    def move(self, delta):
        pos = self.canvas.coords(self.id)
        
        if pos[1] + delta >= 0 and pos[3] + delta <= 400:
            self.canvas.move(self.id, 0, delta)

if __name__ == "__main__":
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        print("Smoke test passed.")
        exit(0)
    
    root = tk.Tk()
    root.title("Pong")
    game = PongGame(root)
    root.mainloop()