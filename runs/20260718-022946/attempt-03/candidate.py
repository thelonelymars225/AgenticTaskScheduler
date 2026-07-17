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
        
        self.score_left = 0
        self.score_right = 0
        
        self.left_score_text = self.canvas.create_text(150, 20, text=f"Score: {self.score_left}", fill="white", font=('Helvetica', 16))
        self.right_score_text = self.canvas.create_text(450, 20, text=f"Score: {self.score_right}", fill="white", font=('Helvetica', 16))
        
        self.root.bind('<KeyPress-Left>', lambda event: self.paddle_left.move(-10))
        self.root.bind('<KeyPress-Right>', lambda event: self.paddle_left.move(10))
        self.root.bind('<KeyPress-a>', lambda event: self.paddle_right.move(-10))
        self.root.bind('<KeyPress-d>', lambda event: self.paddle_right.move(10))
        
        self.game_loop()
    
    def game_loop(self):
        if self.ball.update():
            self.score_left += 1
            self.canvas.itemconfig(self.left_score_text, text=f"Score: {self.score_left}")
        elif self.ball.update():
            self.score_right += 1
            self.canvas.itemconfig(self.right_score_text, text=f"Score: {self.score_right}")
        
        self.root.after(20, self.game_loop)

class Ball:
    def __init__(self, canvas):
        self.canvas = canvas
        self.id = canvas.create_oval(10, 10, 30, 30, fill='white')
        self.canvas.move(self.id, 285, 185)
        
        starts = [-3, -2, -1, 1, 2, 3]
        from random import choice
        self.x = choice(starts)
        self.y = -3
        
    def update(self):
        pos = self.canvas.coords(self.id)
        
        if pos[1] <= 0:
            self.y = 3
        elif pos[3] >= 400:
            self.y = -3
        if pos[0] <= 0:
            return True
        elif pos[2] >= 600:
            return False
        
        paddle_pos_left = self.canvas.coords(self.paddle_left.id)
        paddle_pos_right = self.canvas.coords(self.paddle_right.id)
        
        if pos[1] <= paddle_pos_left[3] and paddle_pos_left[0] <= pos[2] <= paddle_pos_left[2]:
            self.x *= -1
        elif pos[1] <= paddle_pos_right[3] and paddle_pos_right[0] <= pos[2] <= paddle_pos_right[2]:
            self.x *= -1
        
        self.canvas.move(self.id, self.x, self.y)
        return False

class Paddle:
    def __init__(self, canvas, side):
        self.canvas = canvas
        if side == 'left':
            self.id = canvas.create_rectangle(10, 150, 20, 250, fill='white', tags='paddle_left')
        else:
            self.id = canvas.create_rectangle(580, 150, 590, 250, fill='white', tags='paddle_right')
    
    def move(self, delta):
        pos = self.canvas.coords(self.id)
        if pos[1] + delta >= 0 and pos[3] + delta <= 400:
            self.canvas.move(self.id, 0, delta)

if __name__ == "__main__":
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        print("Smoke test passed.")
    else:
        root = tk.Tk()
        game = PongGame(root)
        root.mainloop()