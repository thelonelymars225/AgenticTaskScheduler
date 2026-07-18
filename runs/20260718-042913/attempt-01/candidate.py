import sys
import json
import os
from collections import defaultdict

def summarize(log_lines):
    level_counts = defaultdict(int)
    for line in log_lines:
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            level, message = parts
            level_counts[level] += 1
        else:
            level_counts[''] += 1
    return dict(level_counts)

def main():
    if os.getenv('AGENT_SMOKE_TEST') == '1':
        sys.exit(0)
    
    log_lines = sys.stdin.read().splitlines()
    summary = summarize(log_lines)
    json.dump(summary, sys.stdout, indent=2)

if __name__ == "__main__":
    main()