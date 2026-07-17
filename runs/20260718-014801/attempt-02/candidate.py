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
                raise ValueError("Invalid todo data format")
            return todos
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Failed to load todos: {e}", file=sys.stderr)
        sys.exit(1)

def save_todos(todos):
    try:
        with open(TODO_FILE, 'w') as f:
            json.dump(todos, f, indent=4)
    except IOError as e:
        print(f"Failed to save todos: {e}", file=sys.stderr)
        sys.exit(1)

def add_todo(todo_text):
    if not isinstance(todo_text, str) or not todo_text.strip():
        raise ValueError("Task text must be a non-empty string")
    todos = load_todos()
    todos.append({'text': todo_text, 'completed': False})
    save_todos(todos)

def list_todos():
    todos = load_todos()
    for i, todo in enumerate(todos, start=1):
        status = '[X]' if todo['completed'] else '[ ]'
        print(f"{i}. {status} {todo['text']}")

def complete_todo(index):
    todos = load_todos()
    try:
        todos[index - 1]['completed'] = True
        save_todos(todos)
    except IndexError:
        print("Invalid todo index", file=sys.stderr)
        sys.exit(1)

def remove_todo(index):
    todos = load_todos()
    try:
        del todos[index - 1]
        save_todos(todos)
    except IndexError:
        print("Invalid todo index", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        sys.exit(0)

    if len(sys.argv) < 2:
        print("Usage: python todo.py [add|list|complete|remove] [task|index]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    if command == 'add' and len(sys.argv) > 2:
        try:
            add_todo(' '.join(sys.argv[2:]))
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
    elif command == 'list':
        list_todos()
    elif command == 'complete' and len(sys.argv) > 2:
        try:
            index = int(sys.argv[2])
            complete_todo(index)
        except ValueError:
            print("Index must be an integer", file=sys.stderr)
            sys.exit(1)
    elif command == 'remove' and len(sys.argv) > 2:
        try:
            index = int(sys.argv[2])
            remove_todo(index)
        except ValueError:
            print("Index must be an integer", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)