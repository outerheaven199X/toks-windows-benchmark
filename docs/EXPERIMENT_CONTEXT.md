# TOKS ON WINDOWS // EXPERIMENT CONTEXT

ANTIMEME SYSTEMWORKS // CREATIVE UTILITIES DIVISION  
AM-RS-2026 // V1.0_BUILD // P.01

## 01 // THE QUESTION

The experiment asks whether Actual Computer's toks tokenizer works natively on this Windows PC and how its Python encoding API compares with Hugging Face tokenizers on three pinned tokenizer files. It measures text becoming token IDs. It does not run the neural networks that generate new text.

Earlier work in the same project measured GPU model serving through vLLM on RunPod and validated an Ollama benchmark harness. Those are separate experiments. Their generated-token throughput, TTFT, GPU layouts and costs do not measure toks and are not evidence for the tokenizer speedups reported here. The publication contains only the native Windows CPU tokenizer comparison.

## 02 // WHAT WAS BUILT

The upstream project already had Windows C/assembly build and test support. The fork added a native CPython wheel path: build the existing LLVM core as a static Windows library, link it into the Python extension, and package the result for Windows x64. The tokenizer's algorithm and native core were unchanged by those packaging commits.

“AVX2” names the CPU vector-instruction path used by this run. It is not a different project, GPU backend or tokenizer format. The GPU was unused. Native runtime evidence covers CPython 3.12 on one reported CPU. Earlier fork CI also built wheels for CPython 3.10–3.14; it does not substitute for independent hardware measurements on every version or CPU tier.

## 03 // WHY THERE IS A SECOND BENCHMARK

The first benchmark's initial CPU check recorded 99.5% system load. Its ratios were interesting, but its absolute rates were not suitable for an idle-machine claim. Review also identified that warm repetition should not be in the headline, parity should run in separate processes, thread-pool results needed a narrower label, and binary/source provenance needed to travel with the numbers.

Revision 2 used a new process for every library and round, separate parity processes, balanced execution order, startup and per-trial idle gates, and six-round medians with minimum/maximum ranges. Earlier refused or incomplete attempts remain private historical evidence. Only completed run `20261018-183431` supplies this report. Desktop workloads were paused before that run.

## 04 // WHAT THE REVIEW CHANGED

The independent review found no arithmetic changes were needed. It required clearer labels: the five startup CPU samples do not describe the entire run; 18,624 API checks are only 6,240 distinct toks-vs-HF tokenizer/text pairs; UTF-8 conversion occurs inside the first timed call for non-ASCII strings; and overlapping source windows repeat 58–78% of long/batch bytes within each first pass.

The report now states that every toks first pass is too short for reliable in-phase CPU accounting, and that seven of nine rejections occurred only during the supplementary repeated phase. Including rejected first attempts changes affected headline ratios by at most 1.4%. Desktop and work identifiers were removed from the public derivative.

The four measured Python sources remain byte-identical. Corrected presentation is separate from the historical report, and the original audit receipt remains beside a new extended receipt. The reviewer-proposed report-generator patch is saved for a future measured revision. No timing rerun was required for these wording/privacy corrections.

## 05 // WHAT IS ESTABLISHED

The shipped receipts are internally consistent. The exact fork wheel ran native Windows CPython 3.12 tests and produced matching token IDs for this benchmark. All 576 summary values reproduce; all reported figures are tied to raw receipts. A reviewer-built Linux copy reproduces the token IDs and the broad pattern of speedups on different hardware.

What remains unverified is independent attestation of the historical Windows host and execution, an independent Windows binary rebuild by that reviewer, generalization to production text, and native threading scalability. A source hash recorded by a process supports provenance consistency but cannot prove by itself what code actually executed.

## 06 // PUBLICATION MAP

- `BENCHMARK_REPORT.md`: finished technical report with the nine-row headline table and material limits.
- `EDITORIAL_BRIEF.md`: copy/paste summary and facts an editor must preserve.
- `REPRODUCE.md`: archive download, integrity, audit and optional new-run commands.
- `results.tsv` and `all-results.csv`: unrounded machine-readable results.
- `harness/`: inspection copies of the frozen measurement code and auditor.
- Public evidence ZIP: complete reproducible kit, with explicit redactions and its own manifest.
- Hugging Face Space: static presentation of these results, without an inference server or live benchmark.
- Upstream contribution: Windows wheel support, test portability fixes and benchmark documentation. Its test results and commit identity are separate from the historical performance run.

Actual Computer owns and maintains toks. Hugging Face supplies the reference tokenizer implementation and hosts the results page. ANTIMEME SYSTEMWORKS publishes this community experiment; the page does not imply either project's endorsement.

AM-RS-2026 // V1.0_BUILD // P.01
