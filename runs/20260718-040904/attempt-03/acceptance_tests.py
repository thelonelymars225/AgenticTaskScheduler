import os
import json
import sys
import importlib.util
from pathlib import Path

# Load candidate module from environment variable CANDIDATE_PATH
CANDIDATE_PATH = os.environ['CANDIDATE_PATH']
spec = importlib.util.spec_from_file_location('todo', CANDIDATE_PATH)
todo_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(todo_module)

def test_todo():
    # Test add command
    todo_module.add_todo("Buy milk")
    todos = todo_module.load_todos()
    assert len(todos) == 1
    assert todos[0]['text'] == "Buy milk"
    assert not todos[0]['completed']

    # Test list command
    todo_module.list_todos()
    assert Path('todos.json').exists()

    # Test complete command
    todo_module.complete_todo("1")
    todos = todo_module.load_todos()
    assert todos[0]['completed']

    # Test remove command
    todo_module.remove_todo("1")
    todos = todo_module.load_todos()
    assert len(todos) == 0

def test_invalid_input():
    # Test empty todo text
    todo_module.add_todo("")
    assert Path('todos.json').exists()

    # Test invalid index for complete or remove command
    todo_module.complete_todo("abc")
    todo_module.remove_todo("abc")

if __name__ == '__main__':
    test_todo()
    test_invalid_input()