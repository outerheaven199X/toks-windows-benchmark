# Supplied independent review of the ORIGINAL handoff

This review predates the corrections in this public derivative. The original full patch remains in the private copy because its removed context contains private identifiers. The report-only patch is in ../future-run/. Historical claims below describe the original archive, and the Linux measurements belong to the reviewer.

# Independent audit: toks vs Hugging Face, Windows revision 2

Audited: `TOKS_VS_HF_WINDOWS_V2_AUDIT_HANDOFF_2026-10-18.zip`, SHA-256 `6753d37f16a2265b103ce63f6d9084b9ea29599d24e9fd6f118c7779015ab83d` (matches the supplied hash). Completed run: `runs/20261018-183431`. Earlier run directories were inspected as evidence only. No samples from them enter any figure below.

## Verdict

The numbers can be published once the documentation is fixed. No rerun is needed (.8 confidence). Every reported figure recomputes exactly from the raw receipts. Token-ID parity reproduces bit for bit on a second OS with toks built from the audited source pin. A fresh-process rerun on different hardware reproduces the same pattern of ratios, 9â€“26% lower.

Five items block public posting. None of them changes a number:

1. Personal and work identifiers in STATUS.md and the receipts.
2. A false sentence about UTF-8 preparation.
3. A baseline line that reads as covering the whole run.
4. A parity count that overstates the distinct toks-vs-HF comparisons.
5. A "first pass" label on long/batch cells where most bytes repeat within the pass.

Exact patches are in `proposed-docs-and-audit.patch`. Original receipts are untouched.

The one thing that would change this verdict is evidence that the Windows receipts were produced by code other than the hashed sources. That cannot be checked from the archive alone.

## Findings, ranked by impact

### 1. Publication hygiene: identifiers in the kit (blocking)

`STATUS.md` line 37 names two Docker containers from your work stack, with their IDs. `runs/20261018-183431/preparation/docker-*.json` repeat them and add local paths. `live.log` (all three runs), `provenance/native-runtime.json` and `provenance/provenance.json` carry the Windows username, machine name and home-directory paths. `gates/baseline.json` lists desktop process names.

Fix: keep these files in a private audit copy. Ship a public kit without `preparation/`, and with paths redacted in live.log and provenance JSON. The STATUS.md patch removes the container names.

### 2. "Text UTF-8 data is prepared before timing for all libraries" is false (blocking wording)

Source: `RESULTS.md` Method bullet 2 and `report.py` line 38. `load_cell` calls `str.encode()`, which builds a throwaway bytes object and does not populate CPython's cached UTF-8 form of the str. I checked this on CPython 3.12.13 with `sys.getsizeof`: a fresh non-ASCII str grows only after the first toks or HF call, not after `.encode()` (`repro/utf8check.py`).

Non-ASCII inputs: 398 of 1,024 short, 16 of 32 long and 511 of 1,024 batch texts. Each fresh process reloads the texts, so every first pass pays this cost inside its timer, for both libraries. The cost is the same on both sides, so fairness holds and only the sentence is wrong.

Replacement text: "CPython builds and caches the UTF-8 form of non-ASCII inputs during the first timed call that reads them, for every library."

### 3. The baseline line describes only the run-start gate (blocking wording)

The terminal header says "Measured baseline: 2.2-6.4% total CPU". Those are the five run-start samples in `gates/baseline.json`: [6.445, 2.246, 2.637, 2.344, 5.371], mean 3.809. Both figures are correct for that gate.

The 216 per-trial gates accepted samples from 0.39% to 9.96% (mean 3.38%). Eleven of those gates needed more than two samples, and the highest sample seen inside a gate was 22.36%.

Replacement: "Run-start gate: 2.2-6.4% total CPU; per-trial gates <=10%."

### 4. The parity count needs a qualifier (blocking wording)

18,624 is arithmetically right: (1,024 + 32 + 1,024 + 1,024) texts Ã— 2 comparators Ã— 3 tokenizers. However, half of it is HF no-offset checked against HF standard, and batch32-8T reuses the batch32-1T texts (same SHA-256 in `inputs-manifest.json`).

Distinct toks-vs-HF texts: 6,240, which is 2,080 per tokenizer. All matched.

### 5. Long and batch cells measure substantial within-pass reuse (material, label fix)

Window overlap measured from the corpora and the generator in `prepare-original.py`:

| Workload | Timed bytes | Already seen earlier in the same pass |
|---|---:|---:|
| short-512B | 524 KB | 14% (English 0%, code 27%) |
| long-64KiB | 2.10 MB | 58% (English 34%, code 82%) |
| batch32-1T | 4.19 MB | 78% (English 65%, code 91%) |

The headline ratio climbs with reuse: 17â€“22x short, 41â€“48x long, 46â€“56x batch. On Linux, giving each long text a fresh toks object cut toks throughput 2.9x but HF only about 1.4x. The ratio fell from about 49x in-pass to about 24x per text.

That experiment also resets one-time costs such as building the int-object table and first-touching scratch memory, so it is an upper bound on cache dependence, not a clean cache measurement (`repro/coldtext.py`).

The kit discloses overlap but never quantifies it. Patch text adds the percentages. Suggested headline sentence: "17â€“22x on 512-byte inputs; 41â€“56x on long and batched inputs, where 58â€“78% of bytes repeat within the pass."

### 6. The in-phase load check never covers toks first passes (disclosed, add specifics)

`measure()` resolves the other-CPU estimate only when a phase lasts at least 250 ms and uses at least 31.25 ms of process CPU. Resolved headline first passes: 72 of 216, all HF long-64KiB or batch32-1T.

The following first passes were never resolved:
- All toks first passes: medians 4.8 ms (short), 8.7 ms (long), 13.2 ms (batch).
- HF short-512B: 103â€“121 ms.
- All 8-worker first passes.

For those, the only load evidence is the two-sample gate before the timer and the repeated phase after it. Bias direction: undetected load on toks lowers toks, and rejected noisy HF trials remove slow HF samples. Both shrink the ratio, so the guard's blind spots work against toks rather than for it.

### 7. Rejections replace headline samples because of a supplementary phase (minor)

Of the 9 rejected attempts, 7 were triggered by the repeated phase only and 2 by HF first passes (both glm long-64KiB). All 9 are attempt 1, and each slot succeeded on attempt 2. Retries ran immediately in the same order slot, so balance holds.

Counterfactual with the rejected first attempts put back:

| Cell | As reported | Rejected attempts restored |
|---|---:|---:|
| glm long-64KiB | 40.93x | 41.51x |
| qwen long-64KiB | 45.22x | 45.05x |
| glm short-512B | 17.35x | 17.35x |
| deepseek short-512B | 22.04x | 22.04x |
| deepseek batch32-1T | 56.06x | 56.06x |

No selection bias of consequence (.85 confidence). For v3, a noisy repeated phase should invalidate only the repeated data.

### 8. The pre-timer gate makes "first pass" a first pass after at least 2 s idle (minor, conservative for toks)

On Linux, sleeping 2 s between load and the first pass lowered toks first-pass throughput by about 10â€“20%: qwen short 18.7 â†’ 15.2M tok/s, long 33.2 â†’ 28.8M tok/s. A 200 ms busy spin after the sleep did not restore it, so CPU frequency is not the cause. HF was unchanged. This is a different host and OS, so it is directional evidence only (.55 confidence it applies to the Windows numbers).

### 9. The launcher actually used is not in the kit (minor)

`live.log` names `run-quiet-benchmark.ps1` in a local work directory as the host script. The kit ships `RUN_BENCHMARK.ps1`, whose banner says "Other applications and agents are preserved," while STATUS.md records that Claude and Docker were stopped beforehand. The measured Python sources match: all 228 worker and parity receipts record the kit's hashes for benchmark.py, bench_common.py, idle_guard.py and report.py.

### 10. RESULTS.md was edited after generation (disclosed)

The last Method bullet in RESULTS.md differs from what `report.py` emits, and the file says so. `terminal-results.txt` does regenerate byte-identically from `results.json` with the shipped report.py; I checked this in the extended audit. `audit.json` has a later mtime (19:54) than the run (18:48), but its content is identical to the audit output in live.log and to my rerun.

## Item-by-item results

### 1. Integrity and arithmetic: verified

- The ZIP SHA-256 matches. All 424 MANIFEST.sha256.json entries match, and the only file not listed is the manifest itself.
- Tokenizers, inputs, corpora and inputs-manifest.json are byte-identical to revision 1. The tokenizers were checked against the Hub at the pinned revisions in the revision-1 audit: GLM and Qwen by LFS SHA-256, DeepSeek by git blob SHA-1.
- My own recomputation (`scripts/recompute_v2.py`, no kit code imported) covered 216 raw receipts and 576 summary values: median, min, max, MB/s, pooled p50, nearest-rank p95, call counts and median CPU cores (n/a rule included). There were zero mismatches, and every raw receipt is identical to its copy inside results.json. All 72 RESULTS.md rows and 72 CSV rows match.
- Faster-HF selection is correct in every cell. hf_fast wins all 12, by 1.14â€“1.32x over standard.
- Speedups recompute exactly: 17.35x to 56.06x over the nine one-worker cells. Paired same-round ratios agree within 1%.

| Cell | Paired same-round ratio range |
|---|---:|
| glm short-512B | 16.85â€“17.99x |
| qwen short-512B | 20.87â€“22.46x |
| deepseek short-512B | 21.51â€“23.65x |
| glm long-64KiB | 39.77â€“42.13x |
| qwen long-64KiB | 44.33â€“45.86x |
| deepseek long-64KiB | 46.78â€“49.58x |
| glm batch32-1T | 45.32â€“47.43x |
| qwen batch32-1T | 52.13â€“54.71x |
| deepseek batch32-1T | 54.33â€“57.65x |

- Supplied audit: rerun on a copy, 659 checks, identical output. The 659 decomposes as 11 asset hashes + 216 trial checks + 432 summary values.
- Extended audit (patch): 741 checks. It adds balanced-order execution from process creation times (72), rejected-attempt accounting (9) and terminal-table regeneration (1). It also checks 237 distinct process identities: 12 parity + 216 accepted + 9 rejected.

### 2. Measurement fairness: verified, with findings 2, 5, 6 and 8

- 216 distinct timing processes, none sharing (pid, creation time) with any parity process or each other.
- The creation order inside every round matches the declared six permutations in all 12 cells.
- No corpus content is encoded before the first-pass timer. Loading, the empty call and pool startup are outside the timer.
- Per-call latency excludes ID-list disposal. Throughput includes it. ID-list materialization is inside the timer for all three APIs.
- Cross-session check: the GLM cells in the stopped attempt 20261018-182454 gave 17.91x, 41.64x and 46.48x, against 17.35x, 40.93x and 46.23x in the completed run.

### 3. CPU contention and filtering: verified, with findings 3, 6 and 7

- Every accepted worker gate passed at â‰¤10%.
- Windows accounting granularity: GetProcessTimes and GetSystemTimes tick at about 15.6 ms. At the 250 ms and 31.25 ms floors, the estimate error is roughly Â±0.5â€“1 point of total CPU. The 9.48% maximum is within that margin of the 10% limit.
- The guard does not establish zero background work, and the kit does not claim it does.

### 4. Binary and tokenizer provenance: hashes verified; build not reproduced

| Item | Result |
|---|---|
| Wheel SHA-256 | `c15cc2b0â€¦0c76` matches |
| Installed `.pyd` | `234f0c2câ€¦f522` matches, same as revision 1 |
| Non-native wheel members (8) | Match git blobs at pin `ca80a3e` exactly |
| Git bundle | Verifies, complete history, 7 refs |
| `ca80a3e` vs `221c65f` | No changes under python/, src/, include/ or the LLVM script; differences are audit tooling only |
| Pin vs upstream | Upstream master `2ebc390` (matches actual-computer/toks on GitHub) is an ancestor of the pin. The fork changes only packaging (python/setup.py, pyproject.toml, tools/win/build.cmd, a test). Upstream v0.3.2 â†’ master changes nothing under src/, include/ or python/ |
| Published commits | `ca80a3e` and `221c65f` are reachable on github.com/outerheaven199X/toks |
| CI run 39129940066 | Public page shows success at commit 221c65f, plus artifact digests matching `fresh-ci-artifacts.json` |
| PE timestamp | 2026-10-18 13:05:56 UTC, inside that run's window |

The tokenizer core is upstream toks v0.3.2 code. The Windows binding module is compiled by MSVC (/O2) while the core uses LLVM.

Not verified:
- That the shipped wheel bytes equal the CI artifact contents, because downloading artifacts needs a GitHub login.
- Rebuilding the Windows binary, because I have no MSVC/Windows host.

Matching hashes show the binary is the one the receipts describe. They do not show it was independently rebuilt.

### 5. Presentation fixes: confirmed, with wording issues above

| Fix | Status |
|---|---|
| Warm repetition outside the headline | Confirmed |
| 8-worker results labeled as Python call patterns, not native scaling; no 8T ratio in the headline | Confirmed |
| Unresolved CPU estimates show n/a, with raw values kept | Confirmed |
| Min/max beside every median | Confirmed |
| DeepSeek's exact name `deepseek-ai/DeepSeek-V4.1-Flash-1017` in tables and terminal | Confirmed |
| PyPI collision documented; installer pins the wheel by path and hash | Confirmed |

### 6. Independent reproduction

Platform: Linux 6.18 cloud VM, 2 vCPU Intel Xeon (AVX-512 capable, toks forced to the AVX2 tier as on Windows), CPython 3.12.13 (uv; 3.12.14 not available), clang 18.1.3. tokenizers 0.23.2 came from PyPI.

toks 0.3.2 was built from the audited pin `ca80a3e`, checked out from the shipped Git bundle. The only build change was CFLAGS `-Wno-unused-command-line-argument`, because clang 18 rejects a distro flag under -Werror. It is not the Windows binary.

Harness (`repro/linux_v2.py`): the kit's `bench_common.make_call` adapters unmodified, a separate parity process, then a fresh process per library and round in the six declared orders, pinned to one CPU with `taskset`. A two-sample /proc/stat gate at â‰¤10% replaces the Windows gate. First pass only, 1-worker cells only; the 8-worker cells were skipped on a 2-vCPU host.

Parity: zero mismatches in all 9 unique cells. The HF ID SHA-256 digest and token counts match the Windows parity receipts exactly in all 9.

| Cell | Linux toks M tok/s [min..max] | Linux HF fast M tok/s | Linux ratio | Windows ratio |
|---|---:|---:|---:|---:|
| glm short-512B | 12.65 [11.18..15.92] | 0.943 | 13.42x | 17.35x |
| glm long-64KiB | 27.61 [22.28..30.79] | 0.762 | 36.24x | 40.93x |
| glm batch32-1T | 42.72 [39.52..43.67] | 1.128 | 37.89x | 46.23x |
| qwen short-512B | 15.76 [15.36..16.11] | 0.801 | 19.68x | 21.56x |
| qwen long-64KiB | 27.18 [21.18..30.36] | 0.703 | 38.67x | 45.22x |
| qwen batch32-1T | 40.45 [35.72..45.48] | 0.915 | 44.21x | 53.77x |
| deepseek short-512B | 15.56 [11.79..16.66] | 0.871 | 17.86x | 22.04x |
| deepseek long-64KiB | 31.06 [27.90..32.16] | 0.790 | 39.31x | 48.36x |
| deepseek batch32-1T | 40.74 [32.57..47.60] | 0.978 | 41.68x | 56.06x |

The ordering is the same: short lowest, then long, then batch, and GLM short lowest overall. Linux ratios are 9â€“26% lower, and the VM is noisier. The magnitude reproduces; the exact Windows values cannot be authenticated this way.

## What is established, and how

Independently reproduced:
- Archive and manifest integrity.
- All arithmetic and API selection.
- Process separation and balanced order, as recorded.
- Token-ID parity, bit-exact against the receipts, with toks built from the pinned source.
- Tokenizer files equal the Hub at the pinned revisions.
- Wheel members equal the pinned source.
- The pin's core equals upstream v0.3.2.
- The ratio pattern and rough magnitude on a different host.
- The UTF-8 caching behavior and the overlap percentages.

Internally consistent but self-reported:
- Every timing, gate sample, CPU estimate and process identity in the Windows receipts.
- The host description.
- The preparation steps.
- The wheel-to-CI-artifact link (PE timestamp and receipt only).

Not verifiable from here:
- That the run happened on the stated Ryzen 7 9800X3D and Windows build.
- That no unrecorded background work occurred during unresolved phases.
- That a fresh rebuild of the Windows binary would match.
- Behavior on other CPUs, other Python versions, multilingual text or production inputs.

## Files

- `proposed-docs-and-audit.patch`: README.md, STATUS.md, audit_results.py, a new `runs/20261018-183431/ERRATA.md`, and report.py. The report.py hunk is for the next measured revision only, because every worker recorded the current report.py hash and the audit checks it.
- `repro/`: Linux harness, cache, startup and UTF-8 scripts, results JSON and log.
- `scripts/`: independent recomputation, gate and rejection analysis, and table checks.
