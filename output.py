import tkinter as tk
from random import randint

# Constants
WIDTH = 800
HEIGHT = 600
GRID_SIZE = 20
DIFFICULTY_LEVEL = 100  # milliseconds between moves
SCORING_SYSTEM = True  # enable scoring system

class Game:
    def __init__(self):
        """
        Initializes the game with default values.
        """
        self.root = tk.Tk()
        self.root.title("Snake Game")
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT)
        self.canvas.pack()

        self.grid_size = GRID_SIZE
        self.difficulty_level = DIFFICULTY_LEVEL
        self.scoring_system = SCORING_SYSTEM

        self.score = 0
        self.snake_positions = [(200, 200), (180, 200), (160, 200)]
        self.food_position = self.generate_food_position()
        self.direction = "right"
        self.game_over = False
        self.loading_state = True

        self.handle_events()

    def generate_food_position(self) -> tuple:
        """
        Generates a new random position for the food.

        Returns:
            tuple: A tuple containing the x and y coordinates of the food.
        """
        while True:
            x = randint(0, (WIDTH - GRID_SIZE) // GRID_SIZE) * GRID_SIZE
            y = randint(0, (HEIGHT - GRID_SIZE) // GRID_SIZE) * GRID_SIZE
            if (x, y) not in self.snake_positions:
                return x, y

    def draw_snake(self):
        """
        Draws the snake on the canvas.
        """
        for pos in self.snake_positions:
            self.canvas.create_rectangle(pos[0], pos[1], pos[0] + GRID_SIZE, pos[1] + GRID_SIZE, fill="green")

    def draw_food(self):
        """
        Draws the food on the canvas.
        """
        self.canvas.create_oval(self.food_position[0], self.food_position[1],
                               self.food_position[0] + GRID_SIZE, self.food_position[1] + GRID_SIZE, fill="red")

    def update_score(self):
        """
        Updates the score based on user input.
        """
        if self.scoring_system:
            self.score += 10
            self.canvas.delete("score")
            self.canvas.create_text(10, 10, text=f"Score: {self.score}", tag="score")

    def check_collision(self):
        """
        Checks if the snake has collided with the edge of the canvas or itself.
        """
        head = self.snake_positions[0]
        if (head[0] < 0 or head[0] >= WIDTH or
                head[1] < 0 or head[1] >= HEIGHT or
                head in self.snake_positions[1:]):
            self.game_over = True

    def move_snake(self):
        """
        Updates the position of the snake based on user input.
        """
        new_head = None
        if self.direction == "right":
            new_head = (self.snake_positions[0][0] + GRID_SIZE, self.snake_positions[0][1])
        elif self.direction == "left":
            new_head = (self.snake_positions[0][0] - GRID_SIZE, self.snake_positions[0][1])
        elif self.direction == "up":
            new_head = (self.snake_positions[0][0], self.snake_positions[0][1] - GRID_SIZE)
        elif self.direction == "down":
            new_head = (self.snake_positions[0][0], self.snake_positions[0][1] + GRID_SIZE)

        if new_head:
            self.snake_positions.insert(0, new_head)
            if new_head == self.food_position:
                self.food_position = self.generate_food_position()
                self.update_score()
            else:
                self.snake_positions.pop()

    def check_game_over(self):
        """
        Checks if the game is over and displays a message accordingly.
        """
        if self.game_over:
            self.canvas.delete("all")
            self.canvas.create_text(WIDTH // 2, HEIGHT // 2, text="Game Over!", font=("Arial", 24))
            self.root.after(2000, self.restart_game)

    def restart_game(self):
        """
        Restarts the game by resetting its state.
        """
        self.game_over = False
        self.score = 0
        self.snake_positions = [(200, 200), (180, 200), (160, 200)]
        self.food_position = self.generate_food_position()
        self.direction = "right"
        self.loading_state = True

    def load_game(self):
        """
        Loads the game state from memory.
        """
        if not self.loading_state:
            return
        self.canvas.delete("all")
        self.draw_snake()
        self.draw_food()
        self.update_score()
        self.check_collision()
        self.move_snake()
        self.check_game_over()

    def handle_events(self):
        """
        Handles user input events.
        """
        def on_key_press(event):
            if event.keysym == "Escape":
                self.quit_game()
            elif event.keysym == "r":
                self.restart_game()
            elif event.keysym == "Up" and self.direction != "down":
                self.direction = "up"
            elif event.keysym == "Down" and self.direction != "up":
                self.direction = "down"
            elif event.keysym == "Left" and self.direction != "right":
                self.direction = "left"
            elif event.keysym == "Right" and self.direction != "left":
                self.direction = "right"

        self.root.bind("<KeyPress>", on_key_press)

    def quit_game(self):
        """
        Quits the game by displaying a goodbye message.
        """
        self.canvas.delete("all")
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2, text="Goodbye!", font=("Arial", 24))
        self.root.quit()

    def run(self):
        """
        Runs the main loop of the game.
        """
        self.load_game()
        self.root.mainloop()

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"An error occurred: {e}")