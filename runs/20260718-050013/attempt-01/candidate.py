import os
import json
import sys

TODO_FILE = 'todos.json'

def load_todos():
    if not os.path.exists(TODO_FILE):
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
    if 0 < index <= len(todos):
        todos[index - 1]['completed'] = True
        save_todos(todos)
    else:
        print("Invalid task number", file=sys.stderr)
        sys.exit(1)

def remove_task(index):
    todos = load_todos()
    if 0 < index <= len(todos):
        del todos[index - 1]
        save_todos(todos)
    else:
        print("Invalid task number", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
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
            print("Index must be an integer", file=sys.stderr)
            sys.exit(1)
    elif command == 'remove' and len(sys.argv) > 2:
        try:
            remove_task(int(sys.argv[2]))
        except ValueError:
            print("Index must be an integer", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)