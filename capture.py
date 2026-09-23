#!/usr/bin/env python3
"""Save WebFetch hook payloads verbatim to the current task's capture file."""
import json
import pathlib
import sys

payload = json.load(sys.stdin)
if payload.get('tool_name') == 'WebFetch':
    with pathlib.Path(sys.argv[1]).open('a') as output:
        output.write(json.dumps(payload, ensure_ascii=False) + '\n')
