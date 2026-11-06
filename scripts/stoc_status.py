#!/usr/bin/env python3
# Copyright (c) 2026 Christian Reitwiessner. All rights reserved.
# Released under Apache 2.0 license as described in the file LICENSE.
# Authors: Christian Reitwiessner
"""Build the STOC dashboard. Coverage is curated; GitHub/build facts are observed."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import re
import tempfile
import subprocess

ROOT = Path(__file__).resolve().parent.parent
REPO = 'cslib-community/complexitylib'
UPSTREAM = ROOT / '.cache/upstream'
COVERAGE = {'main-results', 'partial', 'obstruction', 'existing', 'not-assessed'}


def git(*args):
    return subprocess.check_output(['git', '-C', str(UPSTREAM), *args], text=True)


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True))


def validate(catalogue, registry):
    ids = [p['id'] for p in catalogue['papers']]
    if len(ids) != len(set(ids)) or any(type(i) is not int or i < 1 for i in ids):
        raise ValueError('Catalogue IDs must be unique positive integers')
    seen = set()
    for p in registry['papers']:
        if p['id'] not in ids or p['id'] in seen or p['coverage'] not in COVERAGE:
            raise ValueError('Invalid or duplicate status record')
        seen.add(p['id'])
        for key in ['scope', 'remaining', 'review_url', 'reviewed_sha', 'source_prefixes']:
            if not p.get(key):
                raise ValueError(f'Missing {key} for submission {p["id"]}')
        if not p['review_url'].startswith('https://github.com/cslib-community/complexitylib/'):
            raise ValueError('Review evidence must link to the repository')
        if len(p['reviewed_sha']) != 40 or any(c not in '0123456789abcdef' for c in p['reviewed_sha']):
            raise ValueError('Review revision must be a full Git SHA')


def check_state(runs, statuses):
    states = [r['conclusion'] if r['status'] == 'completed' else 'pending' for r in runs]
    states += [s['state'] for s in statuses]
    if not states:
        return 'not reported'
    if any(s in {'failure', 'error', 'timed_out', 'cancelled', 'action_required', 'startup_failure'} for s in states):
        return 'failed'
    if any(s not in {'success', 'neutral', 'skipped'} for s in states):
        return 'pending'
    return 'reported checks passed'  # Not a claim that all six required gates ran.


def extract_results(source, path, sha):
    """Extract source locators, not a semantic/main-theorem classification."""
    found = []
    in_comment = 0
    source_lines = source.splitlines()
    for i, line in enumerate(source_lines):
        # Strip nested block and line comments before recognizing declarations.
        clean = ''
        j = 0
        while j < len(line):
            if line[j:j+2] == '/-':
                in_comment += 1
                j += 2
            elif in_comment and line[j:j+2] == '-/':
                in_comment -= 1
                j += 2
            elif not in_comment and line[j:j+2] == '--':
                break
            else:
                if not in_comment:
                    clean += line[j]
                j += 1
        match = re.match(r'^(?:(?:public|protected|noncomputable)\s+)*(?:@\[.*?\]\s*)?(theorem|lemma)\s+([^\s:(]+)', clean.strip())
        if match:
            statement = []
            for part in source_lines[i:i+18]:
                statement.append(part)
                if ':= by' in part or ' := ' in part:
                    break
            text = '\n'.join(statement).split(':=')[0].strip()
            found.append({'name': match.group(2), 'kind': match.group(1), 'file': path,
                          'line': i+1, 'statement': text[:2400],
                          'url': f'https://github.com/{REPO}/blob/{sha}/{path}#L{i+1}'})
    return found


def resources_for(paper_id, resources):
    events = [r for r in resources['measurements'] if r['paper_id'] == paper_id]
    seconds = sum((dt.datetime.fromisoformat(r['finished_at'].replace('Z', '+00:00')) -
                   dt.datetime.fromisoformat(r['started_at'].replace('Z', '+00:00'))).total_seconds()
                  for r in events)
    tokens = [r.get('total_tokens') for r in events]
    known = [n for n in tokens if n is not None]
    return {'recorded_seconds': seconds if events else None, 'recorded_tasks': len(events),
            'tokens': sum(known) if known else None,
            'token_coverage': f'{len(known)}/{len(events)} recorded tasks',
            'budget': resources.get('paper_budgets', {}).get(str(paper_id), {'time_hours': None, 'tokens': None}),
            'measurements': events}


def source_count(sha, prefixes):
    paths = [p for p in git('ls-tree', '-r', '--name-only', sha, 'Complexity').splitlines()
             if p.endswith('.lean') and any(p.startswith(prefix) for prefix in prefixes)]
    if not paths:
        raise ValueError(f'No library files match {prefixes}')
    lines = 0
    results = []
    for path in paths:
        source = git('show', f'{sha}:{path}')
        lines += len(source.splitlines())
        results.extend(extract_results(source, path, sha))
    return {'lines': lines, 'files': len(paths), 'revision': sha, 'paths': paths, 'results': results}


def observe(pr_number):
    pr = api(f'repos/{REPO}/pulls/{pr_number}')
    sha = pr['head']['sha']
    runs = api(f'repos/{REPO}/commits/{sha}/check-runs?per_page=100')
    statuses = api(f'repos/{REPO}/commits/{sha}/status?per_page=100')
    if runs.get('total_count', 0) > 100 or len(statuses.get('statuses', [])) >= 100:
        raise ValueError('Check list exceeds page size; do not publish an incomplete aggregate')
    # Reruns may leave multiple entries for a name; retain the newest observed entry.
    latest = {}
    for run in sorted(runs['check_runs'], key=lambda r: r['id']):
        latest[run['name']] = run
    latest_status = {}
    for status in reversed(statuses['statuses']):
        latest_status[status['context']] = status
    return {'number': pr_number, 'url': pr['html_url'], 'head': sha,
            'state': 'merged' if pr['merged'] else pr['state'],
            'draft': pr['draft'], 'checks': check_state(list(latest.values()), list(latest_status.values())),
            'checks_url': pr['html_url'] + '/checks'}


def build(output, live=False):
    resources = json.loads((ROOT / 'stoc/resources.json').read_text())
    catalogue = json.loads((ROOT / 'stoc/catalogue.json').read_text())
    registry = json.loads((ROOT / 'stoc/status.json').read_text())
    validate(catalogue, registry)
    observations = {}
    if live:
        for number in sorted({p['pr'] for p in registry['papers']}):
            observations[number] = observe(number)  # Failure aborts; never silently publish stale facts.
    if live:
        revisions = {p['reviewed_sha'] for p in registry['papers']}
        revisions.update(p['head'] for p in observations.values())
        # One fetch avoids overlapping shallow-boundary rewrites across related PR stacks.
        subprocess.run(['git', '-C', str(UPSTREAM), '-c', 'gc.auto=0', 'fetch',
                        '--depth=1', '--no-auto-maintenance', '--no-tags', '--no-write-fetch-head',
                        'origin', *sorted(revisions)], check=True, stdout=subprocess.DEVNULL)
    tracked = {}
    for record in registry['papers']:
        record = dict(record)
        pr = observations.get(record['pr'])
        sha = pr['head'] if pr else record['reviewed_sha']
        record['resources'] = resources_for(record['id'], resources)
        record['source'] = source_count(sha, record['source_prefixes'])
        record['pr_observation'] = pr
        record['review_is_current_head'] = bool(pr and pr['head'] == record['reviewed_sha'])
        tracked[record['id']] = record
    papers = []
    for metadata in catalogue['papers']:
        papers.append({**metadata, **tracked.get(metadata['id'], {'coverage': 'not-assessed'})})
    data = {'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
            'github_observed': live, 'registry_updated': registry['updated'],
            'catalogue_source': catalogue['source'], 'catalogue_updated': catalogue['source_updated'],
            'project_budget': resources['project_budget'], 'resource_notes': [resources['time_semantics'], resources['token_semantics']],
            'papers': sorted(papers, key=lambda p: p['id'])}
    output.mkdir(parents=True, exist_ok=True)
    for name in ['index.html', 'style.css', 'app.js']:
        shutil.copyfile(ROOT / 'stoc' / name, output / name)
    (output / 'data.json').write_text(json.dumps(data, ensure_ascii=False) + '\n')
    print(f'Built {len(papers)} submissions ({len(tracked)} tracked) in {output}')
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'stoc/build')
    parser.add_argument('--upstream', type=Path, default=UPSTREAM, help='Separate source repository used for immutable Git reads')
    parser.add_argument('--github', action='store_true', help='Refresh PR heads/checks and count their current source')
    args = parser.parse_args()
    UPSTREAM = args.upstream.resolve()
    if args.github and UPSTREAM != (ROOT / '.cache/upstream').resolve():
        parser.error('--github must use the dashboard-owned default cache; --upstream is read-only/offline')
    if args.github and not (UPSTREAM / '.git').exists():
        UPSTREAM.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'init', str(UPSTREAM)], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(['git', '-C', str(UPSTREAM), 'remote', 'add', 'origin', f'https://github.com/{REPO}.git'], check=True)
    build(args.output, args.github)
