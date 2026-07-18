import os
import sys
import importlib.util
from pathlib import Path
from tempfile import NamedTemporaryFile

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("todo", CANDIDATE_PATH)
todo = importlib.util.module_from_spec(spec)
sys.modules["todo"] = todo
spec.loader.exec_module(todo)

def test_todo():
    # Test valid case: add task and list tasks
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        os.environ['TODO_FILE'] = f.name
        todo.add_task('Buy milk')
        todo.list_tasks()

    # Test invalid case: try to complete a non-existent task
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        os.environ['TODO_FILE'] = f.name
        todo.complete_task(1)

if __name__ == '__main__':
    test_todo()