"""Presentation: one-thread first-pass headline; repeated text and thread-pool calls in appendix."""
import csv


def best_hf(libs):
    return max(('hf', 'hf_fast'), key=lambda name: libs[name]['tokens_per_second'])


def display(data):
    from benchmark import LABELS
    baseline = data['baseline']['accepted_samples_percent']
    lines = [f"TOKS vs HUGGING FACE | {data['host']['cpu']['Name'].strip()} | Native Windows AVX2",
             f"Measured baseline: {min(baseline):.1f}-{max(baseline):.1f}% total CPU; required <=10%. Independent-process parity.",
             'ONE WORKER | First corpus pass in a fresh process per trial | Six-round median [min..max]', '',
             f"{'Exact tokenizer':<25} {'Workload':<12} {'toks M tok/s [min..max]':>26} {'HF M tok/s [min..max]':>26} {'Ratio':>8}", '-' * 103]
    for row in data['rows']:
        if row['workload']['threads'] != 1:
            continue
        libraries = row['summary']['first_pass']
        t, h = libraries['toks'], libraries[best_hf(libraries)]
        ts = f"{t['tokens_per_second']/1e6:.2f} [{t['min_tokens_per_second']/1e6:.2f}..{t['max_tokens_per_second']/1e6:.2f}]"
        hs = f"{h['tokens_per_second']/1e6:.2f} [{h['min_tokens_per_second']/1e6:.2f}..{h['max_tokens_per_second']/1e6:.2f}]"
        lines.append(f"{LABELS[row['model']['directory']]:<25} {row['workload']['name']:<12} {ts:>26} {hs:>26} {t['tokens_per_second']/h['tokens_per_second']:>7.2f}x")
    lines += ['-' * 103, 'M tok/s = million input tokens/sec. CPU tokenization, no LLM generation or TTFT.',
              'HF uses its faster measured standard/no-offset API. Same IDs for every input.',
              'Mixed English/code slices overlap. Piece caches start empty and fill within a pass.',
              'Warm repetition and 8-worker Python-call comparisons are supplementary in RESULTS.md.',
              'p50/p95 latency, MB/s, CPU-load attribution and complete round receipts are included.']
    return '\n'.join(lines)


def report(output, data):
    screen = display(data)
    (output / 'terminal-results.txt').write_text(screen + '\n', encoding='utf-8')
    lines = ['# Windows tokenizer benchmark, revision 2', '', '```text', screen, '```', '',
             '## Method', '',
             '- Separate parity subprocesses check both measured API variants against Hugging Face standard IDs on every input before performance testing. Those processes exit. Each library/round then runs in a newly created timing process and encodes no corpus content before the first-pass timer.',
             '- Tokenizer/model loading, empty-call initialization and thread-pool startup are excluded. CPU and OS caches are not flushed. Text UTF-8 data is prepared before timing for all libraries. First pass means a fresh tokenizer cache that fills during the corpus pass, not a fresh cache for every string.',
             '- Six permutations of toks, HF standard and HF no-offset fast form six balanced rounds. The headline compares medians and uses the faster HF median. Min/max are measured round rates for the selected API, not confidence intervals. Latencies are pooled per-call samples, with nearest-rank p95.',
             '- Identical pinned tokenizer files and deterministic inputs as revision 1. Corpus: equal numbers of English public-domain prose and CPython source slices. Windows overlap within source text. These are workload-specific results, not a production workload estimate.',
             '- Startup requires five consecutive one-second total CPU samples <=10%. Every timing worker, after loading, requires two consecutive one-second samples <=10%. Failure within the configured timeout exits 3 without a completed table.',
             '- During measured phases >=250 ms with >=31.25 ms process CPU time, the runner estimates other work as total system CPU minus benchmark-process CPU. An estimate above 10% rejects and preserves that attempt, with at most three attempts. This estimate has Windows accounting error; short phases cannot resolve it and report n/a. These guards do not certify zero background work.',
             '- The 8-worker test compares the same Python ID-list API call patterns as revision 1: toks uses eight Python workers, HF eight Rayon workers. Python list materialization/dispatch can limit scaling. This is supplementary application-call performance, not a claim about native kernel scaling; encode_into was not measured.',
             '- Repeated-text measurements deliberately reuse the corpus and tokenizer caches. They are supplementary and excluded from the headline.',
             '- No shared process is killed or suspended; no power, affinity or priority settings are changed.', '',
             '## Host and baseline', '',
             f"Initial accepted CPU samples: {data['baseline']['accepted_samples_percent']}. Full samples and process attribution: gates/baseline.json.",
             f"Run: {data['started_utc']} to {data['finished_utc']}. Host metadata: host.json in the kit.", '',
             '## All measurements, including supplementary calls and repeated input', '',
             '| Exact model | Workload | State | API | Median tok/s | Min tok/s | Max tok/s | MB/s | p50 ms | p95 ms | CPU cores |',
             '|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    with (output / 'results.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['model', 'workload', 'state', 'api', 'median_tok_s', 'min_tok_s', 'max_tok_s', 'MB_s', 'p50_ms', 'p95_ms', 'cores'])
        for row in data['rows']:
            for state, libs in row['summary'].items():
                for lib, s in libs.items():
                    numbers = [s[k] for k in ('tokens_per_second', 'min_tokens_per_second', 'max_tokens_per_second', 'MB_per_second', 'p50_ms', 'p95_ms', 'median_cpu_cores')]
                    writer.writerow([row['model']['id'], row['workload']['name'], state, lib] + numbers)
                    core = f"{s['median_cpu_cores']:.2f}" if s['median_cpu_cores'] is not None else 'n/a'
                    lines.append(f"| {row['model']['id']} | {row['workload']['name']} | {state} | {lib} | {numbers[0]:,.0f} | {numbers[1]:,.0f} | {numbers[2]:,.0f} | {numbers[3]:.2f} | {numbers[4]:.4f} | {numbers[5]:.4f} | {core} |")
    (output / 'RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
