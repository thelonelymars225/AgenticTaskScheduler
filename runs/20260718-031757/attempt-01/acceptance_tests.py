import os
import json
import sys
import importlib.util
from pathlib import Path

TODO_FILE = 'todos.json'

def load_todos():
    if not Path(TODO_FILE).exists():
        return []
    try:
        with open(TODO_FILE, 'r') as f:
            todos = json.load(f)
            if not isinstance(todos, list):
                raise ValueError("Invalid todo data")
            for todo in todos:
                if not isinstance(todo, dict) or 'task' not in todo or 'completed' not in todo:
                    raise ValueError("Invalid todo item")
            return todos
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error loading todos: {e}", file=sys.stderr)
        sys.exit(1)

def save_todos(todos):
    try:
        with open(TODO_FILE, 'w') as f:
            json.dump(todos, f, indent=4)
    except IOError as e:
        print(f"Error saving todos: {e}", file=sys.stderr)
        sys.exit(1)

def add_task(task):
    todos = load_todos()
    todos.append({'task': task, 'completed': False})
    save_todos(todos)

def list_tasks():
    todos = load_todos()
    for i, todo in enumerate(todos, start=1):
        status = '[X]' if todo['completed'] else '[ ]'
        print(f"{i}. {status} {todo['task']}")

def complete_task(index):
    todos = load_todos()
    try:
        index -= 1
        if not (0 <= index < len(todos)):
            raise IndexError("Task index out of range")
        todos[index]['completed'] = True
        save_todos(todos)
    except IndexError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def remove_task(index):
    todos = load_todos()
    try:
        index -= 1
        if not (0 <= index < len(todos)):
            raise IndexError("Task index out of range")
        del todos[index]
        save_todos(todos)
    except IndexError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        sys.exit(0)

    if len(sys.argv) < 2:
        print("Usage: python todo.py [add|list|complete|remove] [task|index]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    if command == 'add' and len(sys.argv) > 2:
        add_task(' '.join(sys.argv[2:]))
    elif command == 'list':
        list_tasks()
    elif command == 'complete' and len(sys.argv) > 2:
        try:
            complete_task(int(sys.argv[2]))
        except ValueError:
            print("Error: Index must be an integer", file=sys.stderr)
            sys.exit(1)
    elif command == 'remove' and len(sys.argv) > 2:
        try:
            remove_task(int(sys.argv[2]))
        except ValueError:
            print("Error: Index must be an integer", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown command or missing argument for {command}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

# Test the candidate
candidate_path = os.environ['CANDIDATE_PATH']
spec = importlib.util.spec_from_file_location('todo', candidate_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Test add_task function
add_task("Buy milk")
load_todos()
assert len(load_todos()) == 1

# Test list_tasks function
list_tasks()

# Test complete_task function
complete_task(1)
load_todos()
assert load_todos()[0]['completed']

# Test remove_task function
remove_task(1)
load_todos()
assert len(load_todos()) == 0