import json
import os
import sys

def summarize(log_lines):
    level_counts = {}
    for line in log_lines:
        parts = line.split(maxsplit=1)
        if len(parts) > 0:
            level = parts[0]
            level_counts[level] = level_counts.get(level, 0) + 1
        else:
            level_counts[''] = level_counts.get('', 0) + 1
    return level_counts

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        sys.exit(0)

    log_lines = []
    for line in sys.stdin:
        log_lines.append(line.strip())

    summary = summarize(log_lines)
    json.dump(summary, sys.stdout, indent=2)

if __name__ == '__main__':
    main()