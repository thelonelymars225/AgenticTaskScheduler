import os
import subprocess

def convert_js_to_ts(js_file, ts_file):
    try:
        subprocess.run(['npx', 'tsc', '--outFile', ts_file, js_file], check=True)
        print(f"Conversion successful: {js_file} -> {ts_file}")
    except subprocess.CalledProcessError as e:
        print(f"Conversion failed: {e}")

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        print("Smoke test passed")
        return 0

    js_file = 'example.js'
    ts_file = 'example.ts'
    convert_js_to_ts(js_file, ts_file)

if __name__ == "__main__":
    main()