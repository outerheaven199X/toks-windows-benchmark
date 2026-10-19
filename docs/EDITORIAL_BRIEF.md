# EDITORIAL BRIEF // TOKS ON WINDOWS

ANTIMEME SYSTEMWORKS // CREATIVE UTILITIES DIVISION
AM-RS-2026 // V1.0_BUILD // P.01

## 01 // READY-TO-USE SUMMARY

We compared Actual Computer's toks 0.3.2 with Hugging Face tokenizers 0.23.2 on native Windows using the tokenizer files from GLM-5.3-Flash, Qwen3.8-27B and DeepSeek-V4.1-Flash-1017. A single worker was 17–22x faster on 512-byte inputs. Long and batched inputs reached 41–56x, with 58–78% of bytes repeated within the pass. All 6,240 distinct tokenizer/text pairs produced matching IDs.

The run used a reported Ryzen 7 9800X3D and CPython 3.12.14 on the AVX2 CPU path. Each library and round ran in a fresh process after an idle gate; parity ran separately. The complete result has 216 accepted timing samples, six balanced execution orders, raw receipts and a reproducible audit. An independent reviewer recomputed all 576 summary values without mismatches and reproduced token-ID parity from source on Linux.

These results measure CPU tokenization, not generated tokens or GPU inference. The long/batch figures include within-pass reuse. Every toks first pass was too short for reliable in-phase background-load accounting. The historical Windows host and execution remain self-reported, and the Windows wheel was not independently rebuilt by the reviewer.

## 02 // FACTS TO KEEP ATTACHED

- 17–22x on 512-byte inputs; 41–56x on long and batched inputs, where 58–78% of bytes repeat within the pass.
- Call the unit “million input tokens per second.” Do not call it model generation speed, GPU TPS or TTFT.
- State “fresh process and tokenizer per trial.” Do not describe the whole corpus as unseen text or imply a fresh cache per string.
- Keep min/max next to medians. Ratios compare medians against the faster HF API, which was the no-offset API in all cells.
- Say 6,240 distinct tokenizer/text pairs. Qualify 18,624 as total API checks, including HF-versus-HF and duplicated batch inputs.
- Name the fork-built Windows wheel and historical source pin. Do not imply an official upstream Windows release or endorsement.
- Keep warm and eight-worker results supplementary. Do not turn this test into a claim about native parallel scaling.
- Say the review checked receipts and independently reproduced Linux parity. Do not call it independently witnessed Windows hardware or a reproducible Windows binary build.
- The publication fixes changed wording and private metadata, not measured figures. No timing rerun was performed for them.

## 03 // HOUSE STYLE

Use ANTIMEME SYSTEMWORKS / CREATIVE UTILITIES DIVISION. Running prose is plain and precise; the brand character lives in short labels and document codes. No superlatives or unsupported performance claims. Tables must remain legible and exact. The Space uses the supplied Default palette and component CSS/JS verbatim, with the existing master header image. The data takes priority over ornament.

## 04 // LINKS

GitHub: https://github.com/outerheaven199X/toks-windows-benchmark
Results Space: https://huggingface.co/spaces/b4ph/toks-windows-benchmark
Upstream project: https://github.com/actual-computer/toks

AM-RS-2026 // V1.0_BUILD // P.01
