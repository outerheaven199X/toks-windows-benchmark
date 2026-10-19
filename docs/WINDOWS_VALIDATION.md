# Windows contribution validation

Contribution commit: `d4a399a186f254265d911ab5deb31809742b8ea7`.

[GitHub Actions run 39182200607](https://github.com/outerheaven199X/toks/actions/runs/39182200607) completed successfully on 2026-10-19 UTC. All six jobs passed: Windows CPython 3.10, 3.11, 3.12, 3.13 and 3.14, plus the Linux regression job.

The Windows jobs built and installed fresh wheels, then exercised the API and thread tests. The 3.12 job also ran the full Python parity profile: 368 tests, 330 passed, 38 skipped, no failures or errors. Its separate API/thread suite reports 32 passed and one skipped; those tests overlap the full suite and are not an additional distinct-test count. The Linux job passed the native and scalar C correctness gates and the existing Unix wheel path.

The fresh CI CPython 3.12 wheel has SHA-256 `2f09369d502206dc41235c5614a71b938a46138eb54d273ad61f74dfa73e7a14`. It is a new build of the contribution branch, not the historical wheel used to measure the published performance table.

The corrected tests were also run on this Windows PC using the historical audited wheel: 330 passed, 38 skipped, no failures or errors. This local check was not a fresh binary rebuild. The skip reasons include intentionally unsupported tokenizer files and unavailable optional reference fixtures.

No performance benchmark was rerun during contribution validation. The public benchmark receipts, frozen sources and historical wheel remain unchanged. CI success establishes the recorded build/test outcomes; it does not independently attest the historical benchmark machine.

No upstream PR exists: GitHub rejected creation under upstream's collaborator-only contribution policy. The pushed branch and patch are available, but contributor sign-off and a permitted maintainer intake route remain unresolved.
