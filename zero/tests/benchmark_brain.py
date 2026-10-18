"""Reproducible local retrieval microbenchmark; no provider-token claims."""
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / 'zeroctl.py'


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        vault = root / 'vault'
        vault.mkdir()
        note = vault / 'demo.md'
        note.write_text('# Demo\n' + ''.join(
            f'Decision {i}: validate contracts with focused tests and preserve local state.\n'
            for i in range(1000)), encoding='utf-8')
        config = root / 'registry.json'
        config.write_text(json.dumps({'version': 1, 'vault': str(vault),
                                     'projects': {'demo': {'note': 'demo.md'}}}), encoding='utf-8')
        times = []
        summary = None
        output_bytes = None
        for _ in range(20):
            start = time.perf_counter()
            result = subprocess.run([sys.executable, str(CLI), 'brain', '--config', str(config),
                                     'recall', 'demo', '--query', 'Decision', '--budget-tokens', '2000'],
                                    capture_output=True, check=True, timeout=10)
            times.append((time.perf_counter() - start) * 1000)
            summary = json.loads(result.stdout.splitlines()[-1])
            output_bytes = len(result.stdout)
        print(json.dumps({'python': platform.python_version(), 'platform': platform.system(),
                          'runs': len(times), 'note_bytes': note.stat().st_size,
                          'retrieval_bytes': summary['output_bytes'], 'total_stdout_bytes': output_bytes,
                          'median_process_ms': round(statistics.median(times), 2),
                          'max_process_ms': round(max(times), 2), 'truncated': summary['truncated'],
                          'provider_tokens': 'NOT RUN; local byte/latency benchmark only'}, indent=2))


if __name__ == '__main__':
    main()
