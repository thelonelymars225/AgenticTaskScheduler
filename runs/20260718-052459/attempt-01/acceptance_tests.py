import json
import importlib.util
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("todo", CANDIDATE_PATH)
todo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(todo)

def test_load_todos():
    todos_path = Path('todos.json')
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        json.dump([], f)
        f.flush()
        os.rename(f.name, todos_path.as_posix())
        assert todo.load_todos() == []
        os.remove(todos_path.as_posix())

def test_add_task():
    todos_path = Path('todos.json')
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        json.dump([], f)
        f.flush()
        os.rename(f.name, todos_path.as_posix())
        todo.add_task("Buy milk")
        assert todo.load_todos() == [{'task': 'Buy milk', 'completed': False}]
        os.remove(todos_path.as_posix())

def test_list_tasks():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        json.dump([{'task': 'Buy milk', 'completed': False}, {'task': 'Walk dog', 'completed': True}], f)
        f.flush()
        todo.list_tasks()

def test_complete_task():
    todos_path = Path('todos.json')
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        json.dump([{'task': 'Buy milk', 'completed': False}, {'task': 'Walk dog', 'completed': True}], f)
        f.flush()
        os.rename(f.name, todos_path.as_posix())
        todo.complete_task(1)
        assert todo.load_todos() == [{'task': 'Buy milk', 'completed': False}, {'task': 'Walk dog', 'completed': True}]
        os.remove(todos_path.as_posix())

def test_remove_task():
    todos_path = Path('todos.json')
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        json.dump([{'task': 'Buy milk', 'completed': False}, {'task': 'Walk dog', 'completed': True}], f)
        f.flush()
        os.rename(f.name, todos_path.as_posix())
        todo.remove_task(1)
        assert todo.load_todos() == [{'task': 'Buy milk', 'completed': False}]
        os.remove(todos_path.as_posix())

def test_invalid_command():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        json.dump([], f)
        f.flush()
        sys.argv = ['todo.py', 'invalid']
        todo.main()

if __name__ == '__main__':
    test_load_todos()
    test_add_task()
    test_list_tasks()
    test_complete_task()
    test_remove_task()
    test_invalid_command()