"""Windows tokenizer benchmark v2: idle-gated, parity and timing in separate processes."""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

from bench_common import cpu_busy, cpu_clock, make_call, quantile, sha, write_json
from idle_guard import IdleRefused, gate, processes, utc

ORDERS = [('toks', 'hf', 'hf_fast'), ('hf', 'hf_fast', 'toks'), ('hf_fast', 'toks', 'hf'),
          ('hf_fast', 'hf', 'toks'), ('toks', 'hf_fast', 'hf'), ('hf', 'toks', 'hf_fast')]
LABELS = {'glm': 'GLM-5.3-Flash', 'qwen': 'Qwen3.8-27B', 'deepseek': 'DeepSeek-V4.1-Flash-1017'}
NATIVE_SHA = '234f0c2c48a5a3a8dfab6edbb861348ed4f640ec6e2668ee104a6f061d76f522'


def runtime():
    import toks
    import tokenizers
    if os.name != 'nt' or sys.version_info[:2] != (3, 12):
        raise RuntimeError('Requires native Windows CPython 3.12.')
    if toks.__version__ != '0.3.2' or tokenizers.__version__ != '0.23.2' or sha(toks._toks.__file__) != NATIVE_SHA:
        raise RuntimeError('Runtime must use the included audited wheel and tokenizers==0.23.2. See README.')
    return {'pid': os.getpid(), 'process_created_filetime': processes()[os.getpid()]['created_filetime'],
            'python': sys.version, 'platform': platform.platform(),
            'toks': toks.__version__, 'tokenizers': tokenizers.__version__, 'extension_sha256': NATIVE_SHA,
            'source_hashes': {name: sha(Path(__file__).with_name(name)) for name in ('benchmark.py', 'bench_common.py', 'idle_guard.py', 'report.py')},
            'environment': {k: os.environ.get(k) for k in ('TOKS_TIER', 'RAYON_NUM_THREADS', 'TOKENIZERS_PARALLELISM')}}


def load_cell(args):
    manifest = json.loads((args.assets / 'inputs-manifest.json').read_text(encoding='utf-8'))
    model = next(m for m in manifest['models'] if m['directory'] == args.model)
    work = next(w for w in manifest['workloads'] if w['name'] == args.workload)
    path = args.assets / model['tokenizer_file']
    data = args.assets / work['file']
    if sha(path) != model['tokenizer_sha256'] or sha(data) != work['sha256']:
        raise RuntimeError('Asset SHA-256 mismatch')
    texts = json.loads(data.read_text(encoding='utf-8'))
    b = work['batch_size']
    inputs = [texts[i:i+b] for i in range(0, len(texts), b)] if b > 1 else texts
    sizes = [sum(len(t.encode()) for t in item) if b > 1 else len(item.encode()) for item in inputs]
    return model, work, path, inputs, sizes


def parity(args):
    info = runtime()
    model, work, path, inputs, sizes = load_cell(args)
    objects = {lib: make_call(lib, path, work['batch_size'], work['threads']) for lib in ('toks', 'hf', 'hf_fast')}
    counts, digest = [], hashlib.sha256()
    for item in inputs:
        expected = objects['hf'][1](item)
        for lib in ('toks', 'hf_fast'):
            if objects[lib][1](item) != expected:
                raise RuntimeError(f'Token-ID mismatch: {model["id"]}, {work["name"]}, {lib}')
        counts.append(sum(map(len, expected)) if work['batch_size'] > 1 else len(expected))
        digest.update(json.dumps(expected, separators=(',', ':')).encode())
        digest.update(b'\n')
    tier = objects['toks'][0].info()['tier']
    for _, _, pool, _ in objects.values():
        if pool:
            pool.shutdown()
    write_json(args.receipt, {'runtime': info, 'model': model, 'workload': work, 'passed': True,
                             'texts_per_comparator': work['texts'], 'comparators': ['toks', 'hf_fast'],
                             'calls': len(inputs), 'ids_per_call': counts, 'ids_per_pass': sum(counts),
                             'bytes_per_pass': sum(sizes), 'ids_sha256': digest.hexdigest(), 'toks_tier': tier})


def measure(call, inputs, sizes, counts, seconds):
    latencies = []
    loops = 0
    before_system = cpu_clock()
    before_cpu = time.process_time_ns()
    begin = time.perf_counter_ns()
    while True:
        for item in inputs:
            t0 = time.perf_counter_ns()
            _ = call(item)
            latencies.append(time.perf_counter_ns() - t0)
            del _  # Keep ID-list disposal outside per-call latency and inside whole-pass throughput.
        loops += 1
        elapsed = time.perf_counter_ns() - begin
        if elapsed >= seconds * 1e9:
            break
    used_cpu = time.process_time_ns() - before_cpu
    busy = cpu_busy(before_system, cpu_clock())
    reliable = elapsed >= 250_000_000 and used_cpu >= 31_250_000
    cores = used_cpu / elapsed if reliable else None
    other = max(0, busy - 100 * cores / os.cpu_count()) if cores is not None else None
    return {'wall_ns': elapsed, 'process_cpu_ns': used_cpu, 'cpu_time_reliable': reliable,
            'process_cpu_cores': cores, 'system_busy_percent': busy, 'estimated_other_cpu_percent': other,
            'passes': loops, 'calls_ns': latencies, 'tokens': sum(counts) * loops, 'bytes': sum(sizes) * loops}


def sample(args):
    info = runtime()
    model, work, path, inputs, sizes = load_cell(args)
    proof = json.loads(args.parity_receipt.read_text(encoding='utf-8'))
    if not proof['passed'] or proof['model'] != model or proof['workload'] != work:
        raise RuntimeError('Missing or mismatched independent-process parity receipt')
    if (info['pid'], info['process_created_filetime']) == (proof['runtime']['pid'], proof['runtime']['process_created_filetime']):
        raise RuntimeError('Parity and timing must run in distinct processes')
    # This process loads exactly one measured implementation and never encodes the parity corpus beforehand.
    obj, call, pool, load_ns = make_call(args.library, path, work['batch_size'], work['threads'])
    tier = obj.info()['tier'] if args.library == 'toks' else None
    baseline = gate(args.max_busy, consecutive=2, timeout=args.idle_timeout, label='after load, before first content')
    gc.collect()
    gc.disable()
    try:
        first = measure(call, inputs, sizes, proof['ids_per_call'], 0)
        for item in inputs:
            call(item)
        repeated = measure(call, inputs, sizes, proof['ids_per_call'], .5)
    finally:
        gc.enable()
        if pool:
            pool.shutdown()
    violations = [name for name, s in (('first_pass', first), ('repeated', repeated))
                  if s['estimated_other_cpu_percent'] is not None and s['estimated_other_cpu_percent'] > args.max_busy]
    receipt = {'runtime': info, 'model': model, 'workload': work, 'library': args.library, 'round': args.round,
               'toks_tier': tier, 'parity_receipt_sha256': sha(args.parity_receipt),
               'parity_process_pid': proof['runtime']['pid'], 'parity_ran_in_this_process': False,
               'baseline': baseline, 'load_and_empty_init_ns': load_ns,
               'first_pass': first, 'repeated': repeated, 'accepted': not violations, 'background_violations': violations}
    write_json(args.receipt, receipt)
    if violations:
        print(f'  Trial rejected: estimated background CPU exceeded {args.max_busy}% during {violations}', flush=True)
        return 4
    return 0


def stats(samples, state):
    xs = [sample[state] for sample in samples]
    rates = [x['tokens'] * 1e9 / x['wall_ns'] for x in xs]
    ms = [ns / 1e6 for x in xs for ns in x['calls_ns']]
    cores = [x['process_cpu_cores'] for x in xs if x['process_cpu_cores'] is not None]
    return {'tokens_per_second': statistics.median(rates), 'min_tokens_per_second': min(rates), 'max_tokens_per_second': max(rates),
            'MB_per_second': statistics.median(x['bytes'] * 1e3 / x['wall_ns'] for x in xs),
            'p50_ms': statistics.median(ms), 'p95_ms': quantile(ms, .95), 'round_rates': rates,
            'median_cpu_cores': statistics.median(cores) if len(cores) == len(xs) else None,
            'reliable_cpu_rounds': len(cores), 'calls': len(ms)}


def invoke(args, mode, model, work, receipt, extra=()):
    env = dict(os.environ, TOKS_TIER='avx2', RAYON_NUM_THREADS=str(work['threads']), TOKENIZERS_PARALLELISM='true', PYTHONUTF8='1', PYTHONUNBUFFERED='1')
    command = [sys.executable, '-u', str(Path(__file__).resolve()), mode, '--assets', str(args.assets), '--output', str(args.output),
               '--model', model['directory'], '--workload', work['name'], '--receipt', str(receipt),
               '--max-busy', str(args.max_busy), '--idle-timeout', str(args.idle_timeout), *extra]
    return subprocess.run(command, env=env, check=False).returncode


def main_run(args):
    from report import display, report
    if (args.output / 'results.json').exists():
        raise RuntimeError('Refusing to overwrite results. Use a new --output directory.')
    runtime()
    for folder in ('raw', 'parity', 'gates', 'rejected'):
        (args.output / folder).mkdir(parents=True, exist_ok=True)
    manifest = json.loads((args.assets / 'inputs-manifest.json').read_text(encoding='utf-8'))
    started = utc()
    first_baseline = gate(args.max_busy, consecutive=5, timeout=args.idle_timeout, label='run baseline')
    write_json(args.output / 'gates' / 'baseline.json', first_baseline)
    print(f"Baseline passed: {', '.join(f'{x:.1f}%' for x in first_baseline['accepted_samples_percent'])}", flush=True)
    for model in manifest['models']:
        for work in manifest['workloads']:
            proof = args.output / 'parity' / f"{model['directory']}-{work['name']}.json"
            print(f"Parity in separate process: {model['id']} / {work['name']}", flush=True)
            if invoke(args, '--parity', model, work, proof):
                raise RuntimeError('Parity subprocess failed')
    rows = []
    for model in manifest['models']:
        for work in manifest['workloads']:
            cell = f"{model['directory']}-{work['name']}"
            proof = args.output / 'parity' / f'{cell}.json'
            print(f"\n[{len(rows)+1}/12] {model['id']} | {work['name']} | fresh process for every library/trial", flush=True)
            selected = {lib: [] for lib in ('toks', 'hf', 'hf_fast')}
            for number, order in enumerate(ORDERS, 1):
                for lib in order:
                    received = args.output / 'raw' / f'{cell}-r{number}-{lib}.json'
                    for attempt in range(1, 4):
                        code = invoke(args, '--sample', model, work, received,
                                      ('--library', lib, '--round', str(number), '--parity-receipt', str(proof)))
                        if code == 0:
                            break
                        failure = json.loads(received.read_text(encoding='utf-8')) if received.exists() else {}
                        if received.exists():
                            received.replace(args.output / 'rejected' / f'{cell}-r{number}-{lib}-attempt{attempt}.json')
                        if code == 3:
                            raise IdleRefused(failure['idle_gate'])
                        if code != 4 or attempt == 3:
                            raise RuntimeError(f'Worker failed or repeatedly noisy: exit {code}')
                    selected[lib].append(json.loads(received.read_text(encoding='utf-8')))
                rates = {lib: selected[lib][-1]['first_pass']['tokens'] * 1e9 / selected[lib][-1]['first_pass']['wall_ns'] for lib in selected}
                hf = max(rates['hf'], rates['hf_fast'])
                print(f"  Round {number}/6: toks {rates['toks']:,.0f} tok/s | HF {hf:,.0f} tok/s | {rates['toks']/hf:.2f}x", flush=True)
            rows.append({'model': model, 'workload': work, 'parity': json.loads(proof.read_text(encoding='utf-8')),
                         'samples': selected, 'summary': {state: {lib: stats(samples, state) for lib, samples in selected.items()}
                                                        for state in ('first_pass', 'repeated')}})
            write_json(args.output / 'progress.json', {'complete_cells': len(rows), 'total_cells': 12, 'last': cell})
    data = {'schema': 2, 'started_utc': started, 'finished_utc': utc(), 'baseline': first_baseline,
            'host': json.loads((args.output / 'host.json' if (args.output / 'host.json').exists() else args.assets / 'host.json').read_text(encoding='utf-8-sig')),
            'max_other_busy_percent': args.max_busy, 'manifest': manifest, 'rows': rows}
    write_json(args.output / 'results.json', data)
    report(args.output, data)
    if sys.stdout.isatty():
        print('\033[2J\033[H', end='')
    print(display(data), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--assets', type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'run')
    ap.add_argument('--model')
    ap.add_argument('--workload')
    ap.add_argument('--parity', action='store_true')
    ap.add_argument('--sample', action='store_true')
    ap.add_argument('--check-idle', action='store_true')
    ap.add_argument('--receipt', type=Path)
    ap.add_argument('--parity-receipt', type=Path)
    ap.add_argument('--library', choices=['toks', 'hf', 'hf_fast'])
    ap.add_argument('--round', type=int)
    ap.add_argument('--max-busy', type=float, default=10.0)
    ap.add_argument('--idle-timeout', type=float, default=60.0)
    args = ap.parse_args()
    if not 0 <= args.max_busy <= 10:
        ap.error('--max-busy must be between 0 and 10 percent')
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        if args.check_idle:
            check = gate(args.max_busy, consecutive=5, timeout=args.idle_timeout, label='preflight only')
            write_json(args.output / 'idle-check.json', check)
            print(json.dumps(check, indent=2))
        elif args.parity:
            parity(args)
        elif args.sample:
            return sample(args)
        else:
            main_run(args)
    except IdleRefused as exc:
        write_json(args.receipt or args.output / 'idle-refusal.json', {'refused': True, 'idle_gate': exc.receipt, 'exit_code': 3})
        print(str(exc), flush=True)
        return 3
    return 0


if __name__ == '__main__':
    sys.exit(main())
