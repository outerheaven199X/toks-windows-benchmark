# toks / Windows optimization study

`ANTIMEME SYSTEMWORKS // CREATIVE UTILITIES DIVISION`

**Plan only. No overnight run or automation has been started.** Allow roughly eight hours for one measured iteration. A successful outcome may be a defensible finding that a candidate change is not worth keeping.

## 01 / Starting point

Native Windows packaging is already implemented. The contribution builds the existing LLVM core into a CPython `.pyd`; it does not call Bash during tokenization. All five Windows Python build jobs and the Linux regression job passed. The existing tokenizer algorithm and assembly kernels are unchanged.

The published experiment shows fast CPU tokenization with important input-reuse qualifications. Its 8-worker Python-call result does not establish native parallel scaling. An RTX 5090 is unnecessary for the proposed work: this is a CPU tokenizer and Python extension study.

The baseline for new code comparisons is contribution commit `d4a399a186f254265d911ab5deb31809742b8ea7`. Archive new source and binary hashes independently from the historical benchmark. Keep the sealed publication unchanged.

## 02 / Overnight work sequence

| Window | Work | Required output |
|---|---|---|
| Hour 0–1 | Build the baseline locally with pinned LLVM and MSVC. Record compiler flags, CPU features, versions and wheel hashes. Run a short correctness gate. | Reproducible build receipt; verified baseline installation |
| Hour 1–2 | Profile Unicode conversion, native encoding, Python integer/list construction, buffer allocation and thread dispatch separately. Examine existing GIL-release boundaries. | Measured time/cycle breakdown; one specific bottleneck hypothesis |
| Hour 2–4 | Implement at most two small candidates, one at a time. Prefer reducing avoidable allocations or copies when profiling supports it. Test compiler/linker changes separately from source changes. | Minimal patches and before/after receipts, including rejected candidates |
| Hour 4–6 | Compare baseline and candidate in balanced fresh-process trials over pinned input sets. Check single-worker and explicitly labelled multi-worker/buffer paths. | Complete timing records, token-ID parity and uncertainty estimates |
| Hour 6–8 | Run full Python parity and native/scalar regression gates. Rebuild the chosen wheel and verify the final patch. Write the result and limitations. | Auditable bundle; either a justified patch or a documented no-change result |

If profiling or a build takes longer, reduce the number of candidates. Do not cut correctness coverage to fit the schedule. A new algorithm or SIMD kernel rewrite is outside this one-night scope.

## 03 / Measurement design

Use the same three pinned tokenizer families as the publication: `zai-org/GLM-5.3-Flash`, `Qwen/Qwen3.8-27B` and `deepseek-ai/DeepSeek-V4.1-Flash-1017`. No model weights or cloud inference endpoints are needed.

Maintain two declared input families: nonoverlapping source windows for the primary comparison, and the historical overlapping corpus for continuity. Add controlled repeated-input tests as a separate cache experiment. Record UTF-8 byte counts, token counts, exact input hashes and overlap statistics. Include ASCII and non-ASCII input. Do not pre-encode one library's strings while timing conversion for the other.

Use independent parity processes, then fresh timing processes for each API, build and round. Counterbalance baseline/candidate order. Preserve every attempt, including rejected runs. Refuse to start above 10% background CPU, record per-trial load and document timing-resolution limits. Extend measurement with larger sets of distinct inputs where needed; repeatedly encoding the same text would change the question to cache replay.

Report median, min/max, per-round ratios and an uncertainty interval across independent trials. Treat repeated samples from one process as correlated. Report process CPU use only when the measured duration resolves it; otherwise show n/a. Use wall time for end-to-end user-facing throughput and a suitable cycle profiler for internal attribution.

## 04 / APIs and claims

The primary comparison must return equivalent token-ID results with equivalent output semantics. `encode_into` already exists and is useful for measuring the native path with reusable output storage. Report that as a separate buffer API experiment; it cannot replace list-returning HF results in a headline speedup claim.

Inspect the C extension's existing `PyUnicode_AsUTF8AndSize`, list creation and GIL-release paths before changing them. Releasing the GIL is unsafe around Python object access. Any threading change needs shared-tokenizer and per-thread-tokenizer tests, error paths, Unicode edge cases and concurrent-lifetime coverage.

Windows-specific optimization should name the mechanism and observed effect. A portable allocation improvement should be described as portable. Compiler flags must not silently drop support for older CPU tiers.

## 05 / Acceptance and delivery

Predeclare a practical threshold of at least 5% median end-to-end improvement on the representative primary workload, with an interval supporting an improvement and no unexplained regression above 2% in another primary cell. Smaller changes can still be reported, but should not be advertised as a meaningful speedup. These are decision thresholds, not promised outcomes.

All supported-input token IDs must match the baseline and HF. Keep explicit unsupported-tokenizer refusals and out-of-range-ID behavior intact. Require the full Windows Python profile, all Windows wheel build jobs, and Linux native/scalar regression checks before calling a patch ready.

Deliver the exact patch, pinned build commands, wheels, hashes, profiler evidence, raw timings, corpus manifests, all rejected attempts and a concise ANTIMEME report. Publish new performance figures only after the final candidate binary has been measured. Any upstream submission still depends on the repository's permitted intake route and the contributor's explicit sign-off.

`AM-RS-2026 // WINDOWS OPTIMIZATION // PLAN V1 // P.01`
