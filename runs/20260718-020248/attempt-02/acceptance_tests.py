import os
import tkinter as tk
from importlib.util import spec_from_file_location, module_from_spec

# Load candidate from file
candidate_path = os.environ['CANDIDATE_PATH']
spec = spec_from_file_location("module.name", candidate_path)
candidate_module = module_from_spec(spec)
spec.loader.exec_module(candidate_module)

class TestPongGame:
    def test_smoke_test(self):
        if os.getenv('AGENT_SMOKE_TEST') == '1':
            return

        root = tk.Tk()
        game = candidate_module.PongGame(root)
        root.mainloop()

    def test_valid_gameplay(self):
        # Create a fake root to avoid opening a window
        class FakeRoot:
            def __init__(self):
                self.bind = lambda *args: None
                self.after = lambda *args: None

        root = FakeRoot()
        game = candidate_module.PongGame(root)

        # Test keyboard controls
        game.paddle_left.move(-10)
        game.paddle_right.move(10)

        # Test scoring
        assert game.score_left == 0
        game.ball.update()
        assert game.score_left == 1

    def test_invalid_gameplay(self):
        # Create a fake root to avoid opening a window
        class FakeRoot:
            def __init__(self):
                self.bind = lambda *args: None
                self.after = lambda *args: None

        root = FakeRoot()
        game = candidate_module.PongGame(root)

        # Test invalid keyboard controls
        game.paddle_left.move(1000)  # Move paddle out of bounds

if __name__ == "__main__":
    test = TestPongGame()

    if os.getenv('AGENT_SMOKE_TEST') == '1':
        print("Smoke test passed.")
        exit(0)

    test.test_valid_gameplay()
    test.test_invalid_gameplay()