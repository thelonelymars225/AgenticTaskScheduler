import os
import sys
import tempfile
import pathlib
import importlib.util
from unittest.mock import patch

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("todo", CANDIDATE_PATH)
todo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(todo)

def test_todo():
    # Create a temporary todo file
    temp_file = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8')
    os.environ['TODO_FILE'] = temp_file.name

    # Test add command
    todo.add_todo('Buy milk')
    temp_file.flush()
    todos = json.load(temp_file)
    assert len(todos) == 1
    assert todos[0]['text'] == 'Buy milk'
    assert not todos[0]['completed']

    # Test list command
    temp_file.seek(0)
    todo.list_todos()

    # Test complete command
    todo.complete_todo(1)

    # Test remove command
    todo.remove_todo(1)

def test_invalid_index():
    with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
        todo.remove_todo(10)
    assert mock_stderr.getvalue().startswith("Invalid todo index")

if __name__ == '__main__':
    test_todo()
    test_invalid_index()