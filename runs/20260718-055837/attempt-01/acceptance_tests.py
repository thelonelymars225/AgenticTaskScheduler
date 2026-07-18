import os
import json
import sys
import importlib.util
from pathlib import Path

# Load candidate module from environment variable CANDIDATE_PATH
CANDIDATE_PATH = os.environ['CANDIDATE_PATH']
spec = importlib.util.spec_from_file_location('todo', CANDIDATE_PATH)
todo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(todo)

def test_todo():
    # Test add task functionality
    todo.add_task("Buy milk")
    todos = todo.load_todos()
    assert len(todos) == 1
    assert todos[0]['task'] == "Buy milk"
    assert not todos[0]['completed']

    # Test list tasks functionality
    todo.list_tasks()

    # Test complete task functionality
    todo.complete_task(1)
    todos = todo.load_todos()
    assert todos[0]['completed']

    # Test remove task functionality
    todo.remove_task(1)
    todos = todo.load_todos()
    assert len(todos) == 0

def test_invalid_index():
    try:
        todo.complete_task(-1)
        assert False, "Expected IndexError"
    except IndexError as e:
        pass

def test_malformed_data():
    with open(todo.TODO_FILE, 'w') as f:
        json.dump("not a list", f)

    try:
        todo.load_todos()
        assert False, "Expected ValueError"
    except ValueError as e:
        pass

if __name__ == '__main__':
    test_todo()
    test_invalid_index()
    test_malformed_data()