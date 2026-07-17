import os
import sys
from importlib.util import spec_from_file_location, module_from_spec

CANDIDATE_PATH = os.environ['CANDIDATE_PATH']

spec = spec_from_file_location("candidate", CANDIDATE_PATH)
candidate_module = module_from_spec(spec)
sys.modules["candidate"] = candidate_module
spec.loader.exec_module(candidate_module)

def test_valid_usage():
    # Set up the environment to mimic a valid usage scenario
    os.environ['AGENT_SMOKE_TEST'] = '0'
    
    # Run the main function with a valid command and argument
    sys.argv = ['todo.py', 'add', 'Buy milk']
    candidate_module.main()
    
    # Check that the task was added successfully
    todos = candidate_module.load_todos()
    assert len(todos) == 1
    assert todos[0]['task'] == 'Buy milk'
    assert not todos[0]['completed']

def test_invalid_usage():
    # Set up the environment to mimic an invalid usage scenario
    os.environ['AGENT_SMOKE_TEST'] = '0'
    
    # Run the main function with an invalid command and argument
    sys.argv = ['todo.py', 'invalid_command']
    candidate_module.main()
    
    # Check that the error message is printed to stderr
    assert "Unknown command or missing argument for invalid_command" in sys.stderr.getvalue()

def test_invalid_index():
    # Set up the environment to mimic an invalid usage scenario
    os.environ['AGENT_SMOKE_TEST'] = '0'
    
    # Run the main function with a valid command and an invalid index
    sys.argv = ['todo.py', 'complete', '10']
    candidate_module.main()
    
    # Check that the error message is printed to stderr
    assert "Error: Task index out of range" in sys.stderr.getvalue()

def test_load_todos():
    # Set up the environment to mimic a valid usage scenario
    os.environ['AGENT_SMOKE_TEST'] = '0'
    
    # Run the load_todos function with no existing todo file
    todos = candidate_module.load_todos()
    assert len(todos) == 0

def test_save_todos():
    # Set up the environment to mimic a valid usage scenario
    os.environ['AGENT_SMOKE_TEST'] = '0'
    
    # Create a new todo list with one task
    todos = [{'task': 'Buy milk', 'completed': False}]
    candidate_module.save_todos(todos)
    
    # Check that the todo file was saved successfully
    assert os.path.exists('todos.json')

if __name__ == '__main__':
    test_valid_usage()
    test_invalid_usage()
    test_invalid_index()
    test_load_todos()
    test_save_todos()