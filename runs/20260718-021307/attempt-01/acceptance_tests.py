import os
import json
import sys
import importlib.util

# Load candidate module from environment variable CANDIDATE_PATH
candidate_path = os.environ['CANDIDATE_PATH']
spec = importlib.util.spec_from_file_location('todo', candidate_path)
todo_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(todo_module)

def test_todo():
    # Test add task functionality
    todo_module.add_task("Buy milk")
    todos = todo_module.load_todos()
    assert len(todos) == 1

    # Test list tasks functionality
    todo_module.list_tasks()

    # Test complete task functionality
    todo_module.complete_task(1)
    todos = todo_module.load_todos()
    assert todos[0]['completed']

    # Test remove task functionality
    todo_module.remove_task(1)
    todos = todo_module.load_todos()
    assert len(todos) == 0

if __name__ == '__main__':
    test_todo()