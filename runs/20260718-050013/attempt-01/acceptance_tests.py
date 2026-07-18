import importlib.util
import os
import pathlib
import subprocess
import tempfile
import unittest

# Load the candidate module
spec = importlib.util.spec_from_file_location("todo", "path/to/todo.py")
todo_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(todo_module)

class TestTodoApp(unittest.TestCase):

    def test_load_todos(self):
        # Create a temporary todo file with invalid data
        temp_file = pathlib.Path(tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8').name)
        temp_file.write('invalid json')
        temp_file.close()

        self.assertEqual(todo_module.load_todos(), [])

    def test_add_task(self):
        # Add a task and verify it's persisted
        todo_module.add_task("Buy milk")
        todos = todo_module.load_todos()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0]['task'], "Buy milk")

    def test_list_tasks(self):
        # Add some tasks and list them
        todo_module.add_task("Buy milk")
        todo_module.add_task("Walk the dog")
        todos = todo_module.load_todos()
        output = subprocess.check_output(['python', 'todo.py', 'list'])
        self.assertIn(b"1. [ ] Buy milk", output)
        self.assertIn(b"2. [ ] Walk the dog", output)

    def test_complete_task(self):
        # Add a task and complete it
        todo_module.add_task("Buy milk")
        todos = todo_module.load_todos()
        self.assertFalse(todos[0]['completed'])
        todo_module.complete_task(1)
        self.assertTrue(todos[0]['completed'])

    def test_remove_task(self):
        # Add some tasks and remove one
        todo_module.add_task("Buy milk")
        todo_module.add_task("Walk the dog")
        todos = todo_module.load_todos()
        self.assertEqual(len(todos), 2)
        todo_module.remove_task(1)
        self.assertEqual(len(todo_module.load_todos()), 1)

    def test_invalid_command(self):
        # Test an invalid command
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
            f.write('{"task": "Buy milk", "completed": true}')
            f.flush()
            os.environ['CANDIDATE_PATH'] = 'path/to/todo.py'
            self.assertEqual(subprocess.check_output(['python', 'todo.py', 'invalid_command']), b'Unknown command: invalid_command\n')

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)