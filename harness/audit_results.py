"""Recompute rates, check parity separation, CPU guards, source hashes and corpus counts."""
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / 'run'
assets = Path(__file__).resolve().parent
data = json.loads((root / 'results.json').read_text(encoding='utf-8'))
assert data['schema'] == 2 and len(data['rows']) == 12
checks = 0


def checked_gate(gate):
    assert gate['passed']
    assert len(gate['accepted_samples_percent']) == gate['consecutive_required']
    assert all(0 <= x <= gate['threshold_percent'] <= 10 for x in gate['accepted_samples_percent'])


checked_gate(data['baseline'])
for asset in data['manifest']['sources'] + data['manifest']['workloads']:
    path = assets / (asset.get('path') or asset['file'])
    assert hashlib.sha256(path.read_bytes()).hexdigest() == asset['sha256']
    checks += 1
comparisons, calls, tokens, max_background = 0, 0, 0, 0.0
for row in data['rows']:
    cell = f"{row['model']['directory']}-{row['workload']['name']}"
    proof_path = root / 'parity' / f'{cell}.json'
    proof = json.loads(proof_path.read_text(encoding='utf-8'))
    assert proof == row['parity'] and proof['passed']
    comparisons += proof['texts_per_comparator'] * len(proof['comparators'])
    for lib, trials in row['samples'].items():
        assert len(trials) == 6 and sorted(x['round'] for x in trials) == list(range(1, 7))
        for trial in trials:
            saved = root / 'raw' / f"{cell}-r{trial['round']}-{lib}.json"
            assert json.loads(saved.read_text(encoding='utf-8')) == trial
            assert trial['accepted'] and not trial['background_violations']
            checked_gate(trial['baseline'])
            assert trial['parity_receipt_sha256'] == hashlib.sha256(proof_path.read_bytes()).hexdigest()
            rt, pr = trial['runtime'], proof['runtime']
            assert (rt['pid'], rt['process_created_filetime']) != (pr['pid'], pr['process_created_filetime'])
            assert not trial['parity_ran_in_this_process']
            assert rt['extension_sha256'] == '234f0c2c48a5a3a8dfab6edbb861348ed4f640ec6e2668ee104a6f061d76f522'
            for name, expected in rt['source_hashes'].items():
                assert hashlib.sha256((assets / name).read_bytes()).hexdigest() == expected
            checks += 1
            for phase in ('first_pass', 'repeated'):
                x = trial[phase]
                assert x['tokens'] == proof['ids_per_pass'] * x['passes']
                assert x['bytes'] == proof['bytes_per_pass'] * x['passes']
                assert len(x['calls_ns']) == proof['calls'] * x['passes']
                assert sum(x['calls_ns']) <= x['wall_ns'] and min(x['calls_ns']) > 0
                assert x['cpu_time_reliable'] == (x['wall_ns'] >= 250_000_000 and x['process_cpu_ns'] >= 31_250_000)
                if x['cpu_time_reliable']:
                    assert math.isclose(x['process_cpu_cores'], x['process_cpu_ns'] / x['wall_ns'])
                    assert x['estimated_other_cpu_percent'] <= 10
                    max_background = max(max_background, x['estimated_other_cpu_percent'])
                else:
                    assert x['process_cpu_cores'] is None and x['estimated_other_cpu_percent'] is None
                if phase == 'first_pass':
                    assert x['passes'] == 1
                else:
                    assert x['wall_ns'] >= 500_000_000
                calls += len(x['calls_ns'])
                tokens += x['tokens']
        for phase in ('first_pass', 'repeated'):
            xs = [t[phase] for t in trials]
            rates = [x['tokens'] / (x['wall_ns'] / 1e9) for x in xs]
            latency = sorted(ns / 1e6 for x in xs for ns in x['calls_ns'])
            expected = {'tokens_per_second': statistics.median(rates), 'min_tokens_per_second': min(rates), 'max_tokens_per_second': max(rates),
                        'MB_per_second': statistics.median(x['bytes'] / 1e6 / (x['wall_ns'] / 1e9) for x in xs),
                        'p50_ms': statistics.median(latency), 'p95_ms': latency[math.ceil(.95 * len(latency))-1]}
            for name, value in expected.items():
                assert math.isclose(value, row['summary'][phase][lib][name], rel_tol=1e-12)
                checks += 1
            cores = [x['process_cpu_cores'] for x in xs]
            expected_cores = statistics.median(cores) if all(x is not None for x in cores) else None
            assert row['summary'][phase][lib]['median_cpu_cores'] == expected_cores
# Process identity: every timing process is distinct from every other and from every parity process.
ORDERS = [('toks', 'hf', 'hf_fast'), ('hf', 'hf_fast', 'toks'), ('hf_fast', 'toks', 'hf'),
          ('hf_fast', 'hf', 'toks'), ('toks', 'hf_fast', 'hf'), ('hf', 'toks', 'hf_fast')]
identities = set()
for row in data['rows']:
    pr = row['parity']['runtime']
    key = (pr['pid'], pr['process_created_filetime'])
    assert key not in identities
    identities.add(key)
    for lib, trials in row['samples'].items():
        for trial in trials:
            key = (trial['runtime']['pid'], trial['runtime']['process_created_filetime'])
            assert key not in identities
            identities.add(key)
    # Balanced order actually executed: process creation order inside each round matches ORDERS.
    for number, order in enumerate(ORDERS, 1):
        made = {lib: next(t for t in row['samples'][lib] if t['round'] == number)['runtime']['process_created_filetime'] for lib in order}
        assert tuple(sorted(order, key=made.get)) == order
        checks += 1
# Rejected attempts: each is a preserved noisy attempt for a slot that later succeeded within three attempts.
rejected = sorted((root / 'rejected').glob('*.json'))
for path in rejected:
    failed = json.loads(path.read_text(encoding='utf-8'))
    assert failed['background_violations'] and not failed['accepted']
    stem, attempt = path.stem.rsplit('-attempt', 1)
    assert 1 <= int(attempt) <= 2 and (root / 'raw' / f'{stem}.json').exists()
    key = (failed['runtime']['pid'], failed['runtime']['process_created_filetime'])
    assert key not in identities
    identities.add(key)
    checks += 1
# Saved terminal table regenerates from results.json when report.py is the version the run recorded.
recorded_report = data['rows'][0]['samples']['toks'][0]['runtime']['source_hashes']['report.py']
if hashlib.sha256((assets / 'report.py').read_bytes()).hexdigest() == recorded_report:
    sys.path.insert(0, str(assets))
    from report import display  # noqa: E402
    assert (root / 'terminal-results.txt').read_text(encoding='utf-8').rstrip('\n') == display(data)
    checks += 1
receipt = {'passed': True, 'checks': checks, 'rejected_attempts': len(rejected), 'distinct_processes': len(identities), 'parity_text_comparisons': comparisons, 'timed_calls': calls,
           'timed_token_operations': tokens, 'max_estimated_other_cpu_percent': max_background,
           'scope': 'Receipt consistency and observed guard values; not independent hardware verification.'}
output = Path(sys.argv[2]) if len(sys.argv) > 2 else root / 'audit.json'
output.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
