"""Windows CPU baseline guard and read-only process attribution. No process control."""
import ctypes
from ctypes import wintypes as w
import datetime
import os
import time

from bench_common import cpu_clock, cpu_busy


class IdleRefused(RuntimeError):
    def __init__(self, receipt):
        self.receipt = receipt
        super().__init__(f"CPU idle gate refused: did not obtain {receipt['consecutive_required']} consecutive samples <= {receipt['threshold_percent']:.1f}%; latest {receipt['samples_percent'][-1]:.1f}%")


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def quiet(samples, limit, consecutive):
    return len(samples) >= consecutive and all(0 <= value <= limit for value in samples[-consecutive:])


def processes():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)

    class Entry(ctypes.Structure):
        _fields_ = [('size', w.DWORD), ('usage', w.DWORD), ('pid', w.DWORD), ('heap', ctypes.c_size_t),
                    ('module', w.DWORD), ('threads', w.DWORD), ('parent', w.DWORD), ('priority', w.LONG),
                    ('flags', w.DWORD), ('name', w.WCHAR * 260)]

    kernel.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = w.HANDLE
    kernel.Process32FirstW.argtypes = [w.HANDLE, ctypes.POINTER(Entry)]
    kernel.Process32NextW.argtypes = [w.HANDLE, ctypes.POINTER(Entry)]
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.GetProcessTimes.argtypes = [w.HANDLE] + [ctypes.POINTER(ctypes.c_ulonglong)] * 4
    kernel.CloseHandle.argtypes = [w.HANDLE]
    snap = kernel.CreateToolhelp32Snapshot(2, 0)
    if snap == ctypes.c_void_p(-1).value:
        raise ctypes.WinError()
    entry = Entry()
    entry.size = ctypes.sizeof(entry)
    output = {}
    try:
        more = kernel.Process32FirstW(snap, ctypes.byref(entry))
        while more:
            handle = kernel.OpenProcess(0x1000, False, entry.pid)
            if handle:
                times = [ctypes.c_ulonglong() for _ in range(4)]
                try:
                    if kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
                        output[entry.pid] = {'name': entry.name, 'parent_pid': entry.parent,
                                            'created_filetime': times[0].value,
                                            'cpu_ns': (times[2].value + times[3].value) * 100}
                finally:
                    kernel.CloseHandle(handle)
            more = kernel.Process32NextW(snap, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snap)
    return output


def gate(limit=10.0, consecutive=3, timeout=60.0, label='', announce=True):
    first_processes = processes()
    begin = time.perf_counter()
    record = {'label': label, 'pid': os.getpid(), 'started_utc': utc(), 'threshold_percent': limit,
              'consecutive_required': consecutive, 'samples_percent': [], 'passed': False}
    previous = cpu_clock()
    while True:
        time.sleep(1)
        current = cpu_clock()
        busy = max(0, min(100, cpu_busy(previous, current)))
        previous = current
        record['samples_percent'].append(busy)
        if quiet(record['samples_percent'], limit, consecutive):
            record['passed'] = True
            break
        if announce and len(record['samples_percent']) % 10 == 0:
            print(f'  Waiting for idle: CPU {busy:.1f}%, limit {limit:.1f}%', flush=True)
        if time.perf_counter() - begin >= timeout:
            break
    span = time.perf_counter() - begin
    final_processes = processes()
    top = []
    for pid, last in final_processes.items():
        first = first_processes.get(pid)
        if not first or first['created_filetime'] != last['created_filetime']:
            continue
        cores = max(0, (last['cpu_ns'] - first['cpu_ns']) / (span * 1e9))
        if cores > .01:
            top.append({'pid': pid, 'name': last['name'], 'parent_pid': last['parent_pid'],
                        'mean_cores': cores, 'system_percent': 100 * cores / os.cpu_count()})
    record.update(finished_utc=utc(), wall_seconds=span, top_processes=sorted(top, key=lambda v: v['mean_cores'], reverse=True)[:20],
                  accepted_samples_percent=record['samples_percent'][-consecutive:] if record['passed'] else [])
    if not record['passed']:
        raise IdleRefused(record)
    return record
