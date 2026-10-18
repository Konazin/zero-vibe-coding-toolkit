"""Small reproducible retrieval-quality/latency benchmark using a synthetic vault."""
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / 'zeroctl.py'
CASES = [
    {'query': 'PostgreSQL transaction consistency', 'expected': {
        'Projects/Atlas/Decisions/ADR-0001.md', 'Projects/Atlas/Architecture/Data.md'}},
    {'query': 'Redis rate limiting', 'expected': {
        'Projects/Beacon/Engineering/Constraints.md', 'Projects/Beacon/Overview.md'}},
]


def call(config, query):
    result = subprocess.run([sys.executable, str(CLI), 'brain', '--config', str(config),
                             'search', query, '--budget-tokens', '1800', '--max-results', '3'],
                            capture_output=True, text=True, check=True, timeout=10)
    start = result.stdout.rfind('\n{\n')
    summary = json.loads(result.stdout[start + 1:] if start >= 0 else result.stdout)
    records = result.stdout[:start if start >= 0 else len(result.stdout)]
    import re
    sources = [match.split(' | ')[1].split(':', 1)[0]
               for match in re.findall(r'^\[([^\]]+)', records, re.MULTILINE)]
    return sources, summary


def main():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        vault = root / 'vault'
        atlas = vault / 'Projects/Atlas'
        beacon = vault / 'Projects/Beacon'
        for folder in (atlas / 'Architecture', atlas / 'Decisions', beacon / 'Engineering'):
            folder.mkdir(parents=True, exist_ok=True)
        (atlas / 'Overview.md').write_text('# Atlas\nThe Atlas product stores customer accounts.\n', encoding='utf-8')
        (atlas / 'Architecture/Data.md').write_text(
            '# Data architecture\nPostgreSQL transactions preserve account consistency.\n', encoding='utf-8')
        (atlas / 'Decisions/ADR-0001.md').write_text(
            '# ADR-0001: PostgreSQL\nStatus: accepted\n\nPostgreSQL provides durable transaction consistency.\n', encoding='utf-8')
        (beacon / 'Overview.md').write_text('# Beacon\nBeacon uses Redis rate limiting at the API boundary.\n', encoding='utf-8')
        (beacon / 'Engineering/Constraints.md').write_text(
            '# Rate limiting\nRedis limits burst traffic; requests fail closed when quota is unavailable.\n', encoding='utf-8')
        config = root / 'registry.json'
        config.write_text(json.dumps({'version': 1, 'vault': str(vault), 'projects': {
            'atlas': {'note': 'Projects/Atlas/Overview.md', 'root': 'Projects/Atlas'},
            'beacon': {'note': 'Projects/Beacon/Overview.md', 'root': 'Projects/Beacon'}}}), encoding='utf-8')
        case_results = []
        all_ms = []
        for case in CASES:
            times, sources, summary = [], [], None
            for _ in range(5):
                start = time.perf_counter()
                sources, summary = call(config, case['query'])
                times.append((time.perf_counter() - start) * 1000)
            all_ms.extend(times)
            expected = case['expected']
            found = set(sources)
            case_results.append({'query': case['query'], 'expected_sources': sorted(expected),
                                 'retrieved_sources': sources,
                                 'source_coverage': round(len(found & expected) / len(expected), 3),
                                 'irrelevant_sources': sorted(found - expected),
                                 'output_bytes': summary['output_bytes'], 'omitted': summary['omitted'],
                                 'median_ms': round(statistics.median(times), 2)})
        print(json.dumps({'python': platform.python_version(), 'platform': platform.platform(),
                          'queries': len(CASES), 'runs_per_query': 5,
                          'median_search_process_ms': round(statistics.median(all_ms), 2),
                          'cases': case_results,
                          'context_measurement': 'retrieved UTF-8 bytes only; no provider tokens measured'}, indent=2))


if __name__ == '__main__':
    main()
