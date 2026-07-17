import os
import importlib.util
import unittest
from unittest.mock import patch

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("candidate", CANDIDATE_PATH)
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

class TestPongGame(unittest.TestCase):

    def test_valid_game(self):
        with patch('tkinter.Tk') as mock_tk:
            game = candidate_module.PongGame(mock_tk.return_value)
            self.assertIsNotNone(game.ball.id)
            self.assertIsNotNone(game.paddle_left.id)
            self.assertIsNotNone(game.paddle_right.id)

    def test_invalid_game_no_paddles(self):
        with patch('tkinter.Tk') as mock_tk:
            game = candidate_module.PongGame(mock_tk.return_value)
            del game.paddle_left
            with self.assertRaises(AttributeError):
                game.game_loop()

if __name__ == "__main__":
    unittest.main(argv=[], exit=False)