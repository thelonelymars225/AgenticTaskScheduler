import importlib.util
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = importlib.util.spec_from_file_location("todo", CANDIDATE_PATH)
todo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(todo)

def test_valid_usage():
    with NamedTemporaryFile(mode='w', encoding='utf-8') as f:
        Path(f.name).write_text('{"todos": []}')
        os.environ['TODO_FILE'] = f.name
        sys.argv = ['todo.py', 'add', 'Buy milk']
        todo.main()
        assert Path(f.name).read_text() == '{"todos": [{"text": "Buy milk", "completed": false}]}\n'

def test_invalid_usage():
    with NamedTemporaryFile(mode='w', encoding='utf-8') as f:
        Path(f.name).write_text('{"todos": []}')
        os.environ['TODO_FILE'] = f.name
        sys.argv = ['todo.py', 'add']
        todo.main()
        assert Path(f.name).read_text() == '{"todos": [{"text": "Buy milk", "completed": false}]}\n'

def test_list_todos():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        Path(f.name).write_text('{"todos": [{"text": "Buy milk", "completed": false}, {"text": "Walk dog", "completed": true}]}')
        os.environ['TODO_FILE'] = f.name
        sys.argv = ['todo.py', 'list']
        todo.main()
        assert Path(f.name).read_text() == '{"todos": [{"text": "Buy milk", "completed": false}, {"text": "Walk dog", "completed": true}]}\n'

def test_complete_todo():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        Path(f.name).write_text('{"todos": [{"text": "Buy milk", "completed": false}, {"text": "Walk dog", "completed": true}]}')
        os.environ['TODO_FILE'] = f.name
        sys.argv = ['todo.py', 'complete', '1']
        todo.main()
        assert Path(f.name).read_text() == '{"todos": [{"text": "Buy milk", "completed": false}, {"text": "Walk dog", "completed": true}]}\n'

def test_remove_todo():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        Path(f.name).write_text('{"todos": [{"text": "Buy milk", "completed": false}, {"text": "Walk dog", "completed": true}]}')
        os.environ['TODO_FILE'] = f.name
        sys.argv = ['todo.py', 'remove', '1']
        todo.main()
        assert Path(f.name).read_text() == '{"todos": [{"text": "Buy milk", "completed": false}]}\n'

def test_malformed_data():
    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        Path(f.name).write_text('{"todos": 123}')
        os.environ['TODO_FILE'] = f.name
        sys.argv = ['todo.py', 'list']
        todo.main()
        assert Path(f.name).read_text() == '{"todos": []}\n'

if __name__ == '__main__':
    test_valid_usage()
    test_invalid_usage()
    test_list_todos()
    test_complete_todo()
    test_remove_todo()
    test_malformed_data()