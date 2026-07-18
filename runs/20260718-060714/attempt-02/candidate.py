import json
import os
import sys

def summarize(log_lines):
    level_counts = {}
    for line in log_lines:
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            print(f"Error parsing log line: {line}", file=sys.stderr)
            continue
        
        level, message = parts
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        
        if not isinstance(level, str) or level not in valid_levels:
            print(f"Invalid log level: {level} in line: {line}", file=sys.stderr)
            continue
        
        if level not in level_counts:
            level_counts[level] = 0
        level_counts[level] += 1
    
    return level_counts

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        sys.exit(0)

    log_lines = []
    for line in sys.stdin:
        log_lines.append(line.strip())

    if not log_lines:
        print("No input provided", file=sys.stderr)
        return

    summary = summarize(log_lines)
    try:
        json.dump(summary, sys.stdout, indent=4)
    except (TypeError, OverflowError) as e:
        print(f"Failed to serialize JSON: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()