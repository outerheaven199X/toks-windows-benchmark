# TOKS ON WINDOWS // BENCHMARK REPORT

ANTIMEME SYSTEMWORKS // CREATIVE UTILITIES DIVISION  
AM-RS-2026 // V1.0_BUILD // P.01

17–22x on 512-byte inputs; 41–56x on long and batched inputs, where 58–78% of bytes repeat within the pass.

Actual Computer's toks 0.3.2 returned the same token IDs as Hugging Face tokenizers 0.23.2 across 6,240 distinct tokenizer/text pairs. In this native Windows experiment, a single worker encoded the short corpus at 24.75–25.98 million input tokens per second, compared with 1.17–1.43 million for the faster measured Hugging Face API. These are CPU text-to-token-ID rates. They do not measure model generation, GPU inference or TTFT.

The Windows host reports an AMD Ryzen 7 9800X3D with 8 cores and 16 logical processors. The runtime was CPython 3.12.14, and toks selected AVX2. The local RTX 5090 was not used. Hardware and historical execution were not independently observed by the reviewer.

## 01 // RESULTS

Each value is the median of six rounds; brackets show the measured minimum and maximum. Each library/round starts in a separate process with a fresh tokenizer object. The comparator is the faster of HF's standard and no-offset APIs, which was `hf_fast` in every cell. Ratios divide the two medians. Minimum/maximum ranges are not confidence intervals.

| CELL | TOKENIZER | INPUT | TOKS M TOK/S [MIN–MAX] | HF M TOK/S [MIN–MAX] | RATIO | REPEATED BYTES |
|---|---|---|---:|---:|---:|---:|
| C01 | zai-org/GLM-5.3-Flash | 512 B | 24.75 [24.47–25.06] | 1.43 [1.39–1.46] | 17.35 | ≈14% |
| C02 | zai-org/GLM-5.3-Flash | 64 KiB | 53.53 [52.69–53.70] | 1.31 [1.27–1.35] | 40.93 | ≈58% |
| C03 | zai-org/GLM-5.3-Flash | 32 × 4 KiB | 73.05 [72.07–74.98] | 1.58 [1.55–1.59] | 46.23 | ≈78% |
| C04 | Qwen/Qwen3.8-27B | 512 B | 25.24 [25.23–25.79] | 1.17 [1.12–1.21] | 21.56 | ≈14% |
| C05 | Qwen/Qwen3.8-27B | 64 KiB | 53.53 [52.42–53.89] | 1.18 [1.17–1.20] | 45.22 | ≈58% |
| C06 | Qwen/Qwen3.8-27B | 32 × 4 KiB | 73.71 [72.43–74.75] | 1.37 [1.37–1.39] | 53.77 | ≈78% |
| C07 | deepseek-ai/DeepSeek-V4.1-Flash-1017 | 512 B | 25.98 [25.13–27.20] | 1.18 [1.15–1.21] | 22.04 | ≈14% |
| C08 | deepseek-ai/DeepSeek-V4.1-Flash-1017 | 64 KiB | 56.10 [52.54–57.03] | 1.16 [1.12–1.17] | 48.36 | ≈58% |
| C09 | deepseek-ai/DeepSeek-V4.1-Flash-1017 | 32 × 4 KiB | 73.70 [71.70–75.35] | 1.31 [1.31–1.34] | 56.06 | ≈78% |

M TOK/S means million input tokens per second. B and KiB describe input bytes. Batch cells contain 32 texts per call, each targeting 4 KiB. Exact model names identify tokenizer files only; no model weights were loaded. Full, unrounded data are in [results.tsv](../results.tsv); all 72 API/state rows are in [all-results.csv](../all-results.csv).

## 02 // WHAT THE NUMBERS MEAN

The short-input result is the narrowest headline: 17–22x across the three tokenizers. The larger 41–56x figures belong to long and batched inputs with substantial overlap. Roughly 58% of long-cell bytes and 78% of batch-cell bytes have already appeared earlier in the same pass; the code half of the batch corpus repeats about 91%. Short inputs repeat about 14% overall. These percentages describe source-window overlap, not a direct measurement of tokenizer cache hits.

“First pass” means a newly created process and tokenizer whose caches fill as that corpus pass proceeds. It does not mean a fresh cache for every string. CPU and operating-system caches were not flushed. The workload is equal numbers of English prose and Python source slices, not a representative production traffic sample. Per-token throughput also depends on the tokenizer's segmentation, so cross-model rates do not rank model quality or inference speed.

Repeated-text measurements and eight-worker calls are supplementary. Warm repeats intentionally reuse the same inputs and caches. The eight-worker test measures the Python ID-list call pattern, including dispatch and list materialization; it is not a native-kernel scaling result. `encode_into` was not measured.

## 03 // METHOD

The completed run contains 12 workload/tokenizer cells, six balanced permutations of three APIs, 216 accepted timing samples and nine rejected attempts. Twelve separate parity processes exited before timing. All 237 timing, parity and rejected-attempt identities are distinct in the receipts. Only the nine single-worker first-pass cells appear in the headline.

Startup required five consecutive one-second total-CPU samples at or below 10%. Those accepted samples ranged from 2.25% to 6.45%, with a mean of 3.81%. Each timing worker loaded its tokenizer, then required two consecutive samples at or below 10%. Accepted per-trial samples ranged from 0.39% to 9.96%, mean 3.38%; 11 workers needed more than two samples. These gates establish low observed background activity, not an isolated machine.

The in-phase load estimate requires at least 250 ms of elapsed time and 31.25 ms of process CPU time. All 72 toks first passes lasted about 5–13 ms and were unresolved by that check. HF's short and eight-worker first passes were also unresolved. Only 72 of the 216 first passes resolved in-phase load, all HF long or batch-1T cells. The largest resolved estimate of other CPU work across accepted phases was 9.48%.

Seven of nine rejected attempts failed only in the supplementary repeated phase. The whole attempt was replaced. Reintroducing the rejected first attempts changes affected headline ratios by at most 1.4%; the original rejected receipts remain in the public evidence archive.

Tokenizer loading, empty-call initialization and thread-pool startup were excluded. UTF-8 conversion of non-ASCII Python strings occurred during the first timed call for every library. There were 398 non-ASCII short texts, 16 long texts and 511 batch texts. Both libraries paid that conversion cost in their own fresh processes.

## 04 // PARITY AND REVIEW

There are 6,240 distinct toks-vs-HF tokenizer/text pairs: 2,080 texts per tokenizer. Every pair matched. The larger 18,624 API-comparison count also includes HF no-offset versus HF standard and the reuse of one-worker batch texts in the eight-worker cells.

The independent reviewer recomputed all 576 summary values from 216 raw receipts without importing the benchmark's code, with zero mismatches. A source-built Linux AVX2 reproduction matched the Windows token-ID hashes in all nine unique input cells. On that reviewer's different CPU, the fresh-process ratios were 13.4–44.2x. Those are reviewer-supplied measurements, not additional Windows samples and not a rerun by this publisher.

The extended consistency audit passes 741 checks. It verifies numerical recomputation, source and asset hashes, process separation, balanced order, rejected-attempt records and regeneration of the original terminal text. It does not independently authenticate the historical machine or execution. The reviewer did not independently rebuild the Windows binary.

## 05 // REPRODUCIBILITY AND PROVENANCE

The benchmark used a fork-built native Windows wheel, not an upstream Windows release. Do not install the unrelated PyPI package `toks==0.3.2`. The complete public evidence archive includes the exact Windows wheel, pinned tokenizer files, corpora, generated inputs, measured harness sources, raw timing receipts, parity records, CSV, audit tools and source Git bundle.

- Wheel SHA-256: `c15cc2b01b861d26c00d1366e44db0b900df1e9eb65574a4a8330dd4ff7c0c76`.
- Native extension SHA-256: `234f0c2c48a5a3a8dfab6edbb861348ed4f640ec6e2668ee104a6f061d76f522`.
- Audited source pin: `ca80a3ed4a45fdabd934f5b5ff818ac3efc0f3e9`.
- Wheel-build checkout: `221c65f3f2ddf64bec0faaa121e5ef545d344211`; the relevant native build inputs match the source pin.
- Historical fork build: [GitHub Actions run 39129940066](https://github.com/outerheaven199X/toks/actions/runs/39129940066). Artifact retrieval through GitHub may require authentication; the audited wheel is also included in the public ZIP.
- Public ZIP SHA-256: `716833fe83e11ed15d831c3f4d11bfed971be50c1553bae479cb55687fd956f1`.

The public archive is a disclosed derivative. It removes private workstation paths, background-process identities, desktop transcripts and preparation details. It preserves measured source bytes, timing arrays, CPU samples, benchmark process identities, token evidence and every reported figure. The original unredacted files remain in a private archive. `REDACTIONS.json` records the transformations. No performance timing was rerun for the publication corrections.

Read [reproduction instructions](REPRODUCE.md), [the full context](EXPERIMENT_CONTEXT.md) and [the supplied independent review](../evidence/INDEPENDENT_REVIEW.md). [Interactive results](https://huggingface.co/spaces/b4ph/toks-windows-benchmark) · [Source and evidence index](https://github.com/outerheaven199X/toks-windows-benchmark).

AM-RS-2026 // V1.0_BUILD // P.01
