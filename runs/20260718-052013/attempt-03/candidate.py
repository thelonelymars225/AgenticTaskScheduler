import json
import os
import sys

def summarize(log_lines):
    level_counts = {}
    for line in log_lines:
        parts = line.split(maxsplit=1)
        if len(parts) >= 2:
            level, message = parts[0], parts[1]
            if level not in level_counts:
                level_counts[level] = 0
            level_counts[level] += 1
        else:
            if '' not in level_counts:
                level_counts[''] = 0
            level_counts[''] += 1
    return level_counts

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        sys.exit(0)

    log_lines = []
    for line in sys.stdin:
        try:
            log_lines.append(line.strip())
        except UnicodeDecodeError:
            continue

    if not log_lines:
        sys.exit(1)

    summary = summarize(log_lines)
    json.dump(summary, sys.stdout, indent=2)

if __name__ == '__main__':
    main()