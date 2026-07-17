import random
import time
from tkinter import Tk, Canvas, messagebox

# Constants
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 100
BALL_SIZE = 20
FPS = 60
MAX_SCORE = 10
LOADING_ANIMATION_DURATION = 3  # seconds

class Settings:
    """
    Holds constants and configurable settings for the game.
    """
    def __init__(self):
        self.paddle_speed: int = 5
        self.ball_velocity: int = 2

class Paddle:
    """
    Represents a paddle object with movement behavior.
    
    Attributes:
        canvas (tk.Canvas): The canvas on which the paddle is drawn.
        id (int): The ID of the paddle object in the canvas.
        speed (int): The speed at which the paddle moves.
    """
    def __init__(self, canvas: Canvas, x: int, y: int, color: str):
        self.canvas = canvas
        self.id = self.canvas.create_rectangle(x, y, x + PADDLE_WIDTH, y + PADDLE_HEIGHT, fill=color)
        self.speed = Settings().paddle_speed

    def move_up(self) -> None:
        """
        Moves the paddle up if it is not at the top boundary.
        """
        coords = self.canvas.coords(self.id)
        if coords[1] > 0:
            self.canvas.move(self.id, 0, -self.speed)

    def move_down(self) -> None:
        """
        Moves the paddle down if it is not at the bottom boundary.
        """
        coords = self.canvas.coords(self.id)
        if coords[3] < HEIGHT:
            self.canvas.move(self.id, 0, self.speed)

class Ball:
    """
    Represents a ball object with movement and collision detection behavior.
    
    Attributes:
        canvas (tk.Canvas): The canvas on which the ball is drawn.
        id (int): The ID of the ball object in the canvas.
        x_velocity (int): The horizontal velocity of the ball.
        y_velocity (int): The vertical velocity of the ball.
    """
    def __init__(self, canvas: Canvas, x: int, y: int, color: str):
        self.canvas = canvas
        self.id = self.canvas.create_oval(x, y, x + BALL_SIZE, y + BALL_SIZE, fill=color)
        self.x_velocity = Settings().ball_velocity
        self.y_velocity = random.choice([-Settings().ball_velocity, Settings().ball_velocity])

    def move(self) -> None:
        """
        Moves the ball and handles collisions with the canvas boundaries.
        """
        self.canvas.move(self.id, self.x_velocity, self.y_velocity)
        coords = self.canvas.coords(self.id)
        if coords[0] <= 0 or coords[2] >= WIDTH:
            self.x_velocity *= -1
        if coords[1] <= 0 or coords[3] >= HEIGHT:
            self.y_velocity *= -1

class Game:
    """
    Manages the game state, updates, and draws.
    
    Attributes:
        root (Tk): The main application window.
        canvas (Canvas): The canvas on which the game is drawn.
        paddle1 (Paddle): The first player's paddle.
        paddle2 (Paddle): The second player's paddle.
        ball (Ball): The ball object in the game.
        score1 (int): The score of the first player.
        score2 (int): The score of the second player.
        lives (int): The number of lives remaining.
    """
    def __init__(self, root: Tk):
        self.root = root
        self.canvas = Canvas(root, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.paddle1 = Paddle(self.canvas, 0, HEIGHT // 2 - PADDLE_HEIGHT // 2, 'blue')
        self.paddle2 = Paddle(self.canvas, WIDTH - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, 'red')
        self.ball = Ball(self.canvas, WIDTH // 2, HEIGHT // 2, 'white')
        self.score1: int = 0
        self.score2: int = 0
        self.lives: int = 3
        self.game_over: bool = False

        # Bind key events for paddle movement
        self.root.bind("<KeyPress-w>", lambda event: self.paddle1.move_up())
        self.root.bind("<KeyPress-s>", lambda event: self.paddle1.move_down())
        self.root.bind("<KeyPress-Up>", lambda event: self.paddle2.move_up())
        self.root.bind("<KeyPress-Down>", lambda event: self.paddle2.move_down())

    def update(self) -> None:
        """
        Updates the game state by moving paddles and ball, checking for collisions,
        updating scores, and handling win/loss conditions.
        """
        if not self.game_over:
            # Move ball and handle collisions
            self.ball.move()
            ball_coords = self.canvas.coords(self.ball.id)
            paddle1_coords = self.canvas.coords(self.paddle1.id)
            paddle2_coords = self.canvas.coords(self.paddle2.id)

            # Check for collision with paddles
            if (ball_coords[0] <= PADDLE_WIDTH and
                paddle1_coords[1] < ball_coords[1] < paddle1_coords[3]):
                self.ball.x_velocity *= -1
            elif (ball_coords[2] >= WIDTH - PADDLE_WIDTH and
                  paddle2_coords[1] < ball_coords[1] < paddle2_coords[3]):
                self.ball.x_velocity *= -1

            # Check for scoring conditions
            if ball_coords[0] <= 0:
                self.score2 += 1
                self.reset_ball()
            elif ball_coords[2] >= WIDTH:
                self.score1 += 1
                self.reset_ball()

            # Check for win/loss condition
            if self.score1 >= MAX_SCORE or self.score2 >= MAX_SCORE:
                self.game_over = True
                winner = "Player 1" if self.score1 > self.score2 else "Player 2"
                messagebox.showinfo("Game Over", f"{winner} wins!")
                self.restart_game()

    def draw(self) -> None:
        """
        Draws the current state of the game on the canvas.
        """
        self.canvas.delete('all')
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill='black')
        self.canvas.create_rectangle(*self.paddle1.canvas.coords(self.paddle1.id), fill='blue')
        self.canvas.create_rectangle(*self.paddle2.canvas.coords(self.paddle2.id), fill='red')
        self.canvas.create_oval(*self.ball.canvas.coords(self.ball.id), fill='white')
        self.canvas.create_text(WIDTH // 2, 20, text=f'Score: {self.score1} - {self.score2}', font=('Arial', 24))

    def start(self) -> None:
        """
        Starts the game loop with a loading animation.
        """
        self.loading_animation()
        self.root.after(1000 // FPS, self.game_loop)

    def game_loop(self) -> None:
        """
        The main game loop that updates and draws the game state at a fixed frame rate.
        """
        if not self.game_over:
            self.update()
            self.draw()
            self.root.after(1000 // FPS, self.game_loop)

    def loading_animation(self) -> None:
        """
        Displays a loading animation before starting the game.
        """
        for i in range(LOADING_ANIMATION_DURATION):
            self.canvas.delete('all')
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill='black')
            self.canvas.create_text(WIDTH // 2, HEIGHT // 2, text=f'Loading... {i + 1}', font=('Arial', 36), fill='white')
            self.root.update()
            time.sleep(1)

    def reset_ball(self) -> None:
        """
        Resets the ball to the center of the canvas with a random vertical velocity.
        """
        self.canvas.coords(self.ball.id, WIDTH // 2, HEIGHT // 2, WIDTH // 2 + BALL_SIZE, HEIGHT // 2 + BALL_SIZE)
        self.ball.x_velocity = Settings().ball_velocity
        self.ball.y_velocity = random.choice([-Settings().ball_velocity, Settings().ball_velocity])

    def restart_game(self) -> None:
        """
        Restarts the game by resetting scores and lives.
        """
        self.score1 = 0
        self.score2 = 0
        self.lives = 3
        self.game_over = False
        self.reset_ball()
        self.start()

def main() -> None:
    root = Tk()
    root.title("Pong Game")
    game = Game(root)
    game.start()
    root.mainloop()

if __name__ == "__main__":
    main()