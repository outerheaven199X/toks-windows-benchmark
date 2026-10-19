# REPRODUCE // EVIDENCE FIRST

ANTIMEME SYSTEMWORKS // CREATIVE UTILITIES DIVISION  
AM-RS-2026 // V1.0_BUILD // P.01

## 01 // VERIFY THE HISTORICAL RESULT

From this GitHub repository, use Python 3.11 or later. These commands download and audit historical evidence; they do not perform new timing:

```powershell
python tools/download_evidence.py --output evidence/run
$kit = 'evidence/run/toks-vs-hf-windows-v2-public'
python "$kit/audit_results.py" "$kit/runs/20261018-183431" "$kit/runs/20261018-183431/audit-local.json"
python "$kit/independent-review/scripts/recompute_v2.py" "$kit/runs/20261018-183431"
```

Expected audit: 741 checks, 237 process identities, exit 0. Expected independent arithmetic output: 576 summary checks, zero mismatches, 216 timing processes. Read stdout as well as exit codes: the supplied independent script reports numerical mismatches without returning a failure code.

Direct archive: [public evidence ZIP](https://huggingface.co/spaces/b4ph/toks-windows-benchmark/resolve/main/downloads/TOKS_VS_HF_WINDOWS_V2_PUBLIC_2026-10-18.zip). SHA-256: `716833fe83e11ed15d831c3f4d11bfed971be50c1553bae479cb55687fd956f1`. The downloader verifies that hash and safe extraction paths before unpacking. The ZIP's `MANIFEST.sha256.json` supplies per-file hashes. The raw JSON receipts are privacy-redacted derivatives; `REDACTIONS.json` describes the exact changes.

## 02 // DISPLAY THE SAVED TABLE

On Windows, open `SHOW_RESULTS.cmd` inside the extracted kit. This displays the corrected saved result, leaving the terminal available for screenshots. It does not rerun the benchmark.

## 03 // OPTIONAL NEW MEASUREMENT

Use native Windows x64 CPython 3.12. Install from the supplied wheel path, never the unrelated package named `toks==0.3.2` on PyPI. The exact historical setup is described in the kit's README. In the extracted kit:

```powershell
.\INSTALL_ENV.ps1 -Python 'C:\path\to\python.exe'
.\RUN_BENCHMARK.ps1 -Python '.\.venv\Scripts\python.exe' -IdleTimeout 120
```

Replace the explicit Python path with your native CPython 3.12 executable. The installer refuses to overwrite an existing environment. A new measurement creates its own run directory; do not replace the historical run. For corrected generated prose in a future revision, apply `future-run/report.py.patch` in a separate copy before measuring. The current report.py remains frozen to preserve historical source hashes.

Exit codes: 0 complete; 3 idle-gate refusal; 4 rejected noisy worker attempt (controller retries); 1 other error or exhausted retries. Incomplete attempts have no completed comparison table. Leave the 10% idle threshold unchanged. CPU load during very short phases remains unresolved even when the pre-timer gate passes.

AM-RS-2026 // V1.0_BUILD // P.01
