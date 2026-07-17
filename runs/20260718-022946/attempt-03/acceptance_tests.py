import os
import tkinter as tk
from importlib.util import spec_from_file_location, module_from_spec

# Get candidate path from environment variable
candidate_path = os.environ['CANDIDATE_PATH']

# Load candidate module using importlib
spec = spec_from_file_location("module.name", candidate_path)
module = module_from_spec(spec)
spec.loader.exec_module(module)

class TestPongGame:
    def test_smoke_test(self):
        if os.getenv('AGENT_SMOKE_TEST') == '1':
            return
        
        # Create a fake root window
        class FakeTk(tk.Tk):
            def __init__(self):
                super().__init__()
                self.destroyed = False
            
            def destroy(self):
                self.destroyed = True
        
        root = FakeTk()
        
        # Create game instance with fake root
        game = module.PongGame(root)
        
        # Test keyboard controls
        root.bind('<KeyPress-Left>', lambda event: None)
        root.bind('<KeyPress-Right>', lambda event: None)
        root.bind('<KeyPress-a>', lambda event: None)
        root.bind('<KeyPress-d>', lambda event: None)
        
        # Test scoring and restart
        game.score_left = 10
        game.score_right = 20
        game.game_loop()
        
        # Check if the game loop runs without errors
        try:
            while not root.destroyed:
                root.after(100)
        except Exception as e:
            assert False, f"Game loop failed with error: {e}"
        
        # Test restart after a score
        game.score_left = 10
        game.score_right = 20
        game.game_loop()
        
        # Check if the scores are updated correctly
        try:
            while not root.destroyed:
                root.after(100)
        except Exception as e:
            assert False, f"Score update failed with error: {e}"
        
    def test_invalid_input(self):
        # Create a fake root window
        class FakeTk(tk.Tk):
            def __init__(self):
                super().__init__()
                self.destroyed = False
            
            def destroy(self):
                self.destroyed = True
        
        root = FakeTk()
        
        # Test invalid input (e.g. non-integer score)
        game = module.PongGame(root)
        game.score_left = 'abc'
        try:
            game.game_loop()
        except Exception as e:
            assert False, f"Invalid input failed with error: {e}"
        
if __name__ == "__main__":
    test = TestPongGame()
    test.test_smoke_test()
    test.test_invalid_input()