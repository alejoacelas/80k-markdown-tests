#!/usr/bin/env python3
"""Run independent WebFetch experiments and download reference pages afterwards."""
import argparse
import concurrent.futures
import csv
import datetime as dt
import json
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parent


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def execute(command, stdout, stderr, timeout):
    with stdout.open('w') as out, stderr.open('w') as err:
        try:
            return subprocess.run(command, stdin=subprocess.DEVNULL, stdout=out,
                                  stderr=err, timeout=timeout, check=False).returncode
        except subprocess.TimeoutExpired:
            err.write(f'\nTimed out after {timeout} seconds.\n')
            return 124


def read_tasks(path):
    tasks = []
    seen = set()
    with path.open() as source:
        for row in csv.reader(source, delimiter='\t'):
            if not row:
                continue
            if len(row) != 4:
                raise ValueError('Each task must have four tab-separated columns')
            name, condition, url, prompt = row
            if not re.fullmatch(r'[a-z0-9-]+', name) or name in seen:
                raise ValueError(f'Unsafe or duplicate task ID: {name}')
            if not url.startswith(('https://', 'http://')):
                raise ValueError(f'Not an HTTP URL: {url}')
            seen.add(name)
            tasks.append(dict(id=name, historical_condition=condition, url=url, prompt=prompt))
    if not tasks:
        raise ValueError('No tasks found')
    return tasks


def run_task(task, output, version, model, timeout):
    folder = output / task['id']
    folder.mkdir()
    capture = folder / 'calls.jsonl'
    hook = shlex.join([sys.executable, str(ROOT / 'capture.py'), str(capture)])
    settings = {'hooks': {event: [{'matcher': 'WebFetch', 'hooks': [
        {'type': 'command', 'command': hook}]}]
        for event in ('PostToolUse', 'PostToolUseFailure')}}
    prompt = ('Call WebFetch exactly once with this input: ' +
              json.dumps({'url': task['url'], 'prompt': task['prompt']}) +
              '. Do not fetch another URL, even on redirects. Then reply: captured.')
    command = ['claude', '-p', prompt, '--settings', json.dumps(settings),
               '--setting-sources', '', '--tools', 'WebFetch', '--allowedTools', 'WebFetch',
               '--strict-mcp-config', '--disable-slash-commands', '--no-session-persistence',
               '--max-turns', '4', '--output-format', 'json']
    if model:
        command += ['--model', model]
    code = execute(command, folder / 'claude.json', folder / 'claude.stderr', timeout)
    errors = []
    calls = []
    try:
        result = json.loads((folder / 'claude.json').read_text())
        if result.get('is_error'):
            errors.append('Claude reported an error')
    except (ValueError, OSError):
        errors.append('Missing or invalid Claude JSON')
    if code:
        errors.append(f'Claude exited {code}')
    try:
        calls = [json.loads(line) for line in capture.read_text().splitlines() if line]
    except (ValueError, OSError):
        errors.append('Missing or invalid WebFetch capture')
    if len(calls) != 1:
        errors.append(f'Expected one WebFetch call, captured {len(calls)}')
    if len(calls) == 1 and calls[0].get('tool_input') != {'url': task['url'], 'prompt': task['prompt']}:
        errors.append('WebFetch input differs from requested task')
    # A WebFetch failure (e.g. the deliberate 404) is experimental evidence.
    # It is distinct from a runner/authentication/capture failure.
    response = calls[0].get('tool_response', calls[0].get('error', '')) if calls else ''
    text = response.get('result', '') if isinstance(response, dict) else str(response)
    (folder / 'response.txt').write_text(text)
    reference = ['curl', '--silent', '--show-error', '--location', '--compressed',
                 '--max-time', '60', '--proto', '=http,https', '--proto-redir', '=http,https',
                 '-H', 'Accept: text/markdown, text/html, */*',
                 '-A', f'Claude-User (claude-code/{version}; +https://support.anthropic.com/)',
                 '--dump-header', str(folder / 'reference.headers'),
                 '--output', str(folder / 'reference.body'),
                 '--write-out', '%{json}', task['url']]
    ref_code = execute(reference, folder / 'reference.json', folder / 'reference.stderr', 70)
    metadata = {}
    try:
        metadata = json.loads((folder / 'reference.json').read_text())
        body = (folder / 'reference.body').read_text(errors='replace')
    except (ValueError, OSError):
        body = ''
        errors.append('Missing or invalid reference download')
    if ref_code:
        errors.append(f'curl exited {ref_code}')
    row = dict(task, errors=errors, capture_event=calls[0].get('hook_event_name') if calls else None,
               reference_status=metadata.get('http_code'), reference_type=metadata.get('content_type'),
               reference_chars=len(body), response_chars=len(text), response_equals_reference=text == body,
               truncation_marker_in_response='[Content truncated due to length...]' in text)
    save(folder / 'result.json', row)
    print(f"{task['id']}: {'ERROR: ' + '; '.join(errors) if errors else 'captured'}", flush=True)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tasks', type=pathlib.Path, default=ROOT / 'tasks.tsv')
    parser.add_argument('--ids', help='Comma-separated task IDs; default: all 30')
    parser.add_argument('--output', type=pathlib.Path, help='New directory; existing paths are refused')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--timeout', type=int, default=180, help='Seconds per Claude session')
    parser.add_argument('--model', help='Claude model ID; omitted uses your account default')
    args = parser.parse_args()
    if args.jobs < 1 or args.timeout < 1:
        parser.error('jobs and timeout must be positive')
    try:
        tasks = read_tasks(args.tasks)
        if args.ids:
            selected = set(args.ids.split(','))
            missing = selected - {t['id'] for t in tasks}
            if missing:
                raise ValueError(f'Unknown task IDs: {sorted(missing)}')
            tasks = [t for t in tasks if t['id'] in selected]
    except (ValueError, OSError) as error:
        parser.error(str(error))
    for executable in ('claude', 'curl'):
        if not shutil.which(executable):
            parser.error(f'{executable} is required')
    version = subprocess.check_output(['claude', '--version'], text=True).strip()
    output = (args.output or ROOT / 'runs' / (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6])).resolve()
    try:
        output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error(f'Refusing to overwrite {output}')
    save(output / 'manifest.json', dict(started=dt.datetime.now(dt.timezone.utc).isoformat(),
         claude_version=version, requested_model=args.model, python=sys.version,
         tasks=tasks, reference_note='Independent curl downloads after WebFetch; not its internal input'))
    print(f'Outputs: {output}', flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_task, t, output, version.split()[0], args.model, args.timeout) for t in tasks]
        rows = []
        for task, future in zip(tasks, futures):
            try:
                rows.append(future.result())
            except Exception as error:
                rows.append(dict(task, errors=[str(error)]))
    save(output / 'results.json', rows)
    lines = ['# Run results', '', f'Claude Code: {version}', '',
             'Captured means the experiment completed, not that the answer is correct.', '',
             '| Task | Capture | Reference HTTP | Reference type |', '|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['id']} | {'ERROR' if r['errors'] else 'captured'} | {r.get('reference_status', '')} | {r.get('reference_type', '')} |")
    lines += ['', 'Inspect each response.txt against reference.body and reference.headers. Errors are listed in results.json.', '']
    (output / 'results.md').write_text('\n'.join(lines))
    return int(any(r['errors'] for r in rows))


if __name__ == '__main__':
    sys.exit(main())
