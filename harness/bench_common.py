"""Shared encoding adapters, pinned to the original measured call patterns."""
import concurrent.futures
import ctypes
import hashlib
import json
import math
from pathlib import Path
import threading
import time

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    temp = Path(str(path) + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    temp.replace(path)


def cpu_clock():
    idle, kernel, user = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
    if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
        raise ctypes.WinError()
    return idle.value, kernel.value + user.value


def cpu_busy(a, b):
    return 100 * (1 - (b[0] - a[0]) / max(1, b[1] - a[1]))


def quantile(values, q):
    return sorted(values)[max(0, math.ceil(q * len(values)) - 1)]


def make_call(lib, path, batch, threads):
    import toks
    import tokenizers
    begin = time.perf_counter_ns()
    obj = toks.Tokenizer.from_file(str(path)) if lib == 'toks' else tokenizers.Tokenizer.from_file(str(path))
    pool = None
    if lib == 'toks' and batch > 1 and threads > 1:
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=threads)
        barrier = threading.Barrier(threads)

        def start_worker(_):
            barrier.wait()

        list(pool.map(start_worker, range(threads)))

        def encode_chunk(chunk):
            return obj.encode_batch(chunk, add_special_tokens=False)

        def call(texts):
            stride = (len(texts) + threads - 1) // threads
            chunks = [texts[i:i + stride] for i in range(0, len(texts), stride)]
            return [ids for group in pool.map(encode_chunk, chunks) for ids in group]
    elif lib == 'toks' and batch > 1:
        def call(texts):
            return obj.encode_batch(texts, add_special_tokens=False)
    elif lib == 'toks':
        def call(text):
            return obj.encode(text, add_special_tokens=False)
    elif lib == 'hf_fast' and batch > 1:
        def call(texts):
            return [enc.ids for enc in obj.encode_batch_fast(texts, add_special_tokens=False)]
    elif lib == 'hf_fast':
        def call(text):
            return obj.encode_batch_fast([text], add_special_tokens=False)[0].ids
    elif batch > 1:
        def call(texts):
            return [enc.ids for enc in obj.encode_batch(texts, add_special_tokens=False)]
    else:
        def call(text):
            return obj.encode(text, add_special_tokens=False).ids
    # Initialize code/thread pools using no content. Timed text has not been seen by this object.
    call([''] * batch if batch > 1 else '')
    return obj, call, pool, time.perf_counter_ns() - begin
