# M2 Runtime + local Chromium integration

- decision source: `scripted_policy` (deterministic stub, not a model)
- runtime: actual `Runtime.advance`; browser: Chromium via Playwright
- model calls: 0; local synthetic result, not an official score
- harness: `D:\Dwen\Alpha26fall\华为2026Hackathon_WebAgent\02_代码\01_harness\当前版本`; ref: `working-after-scope-and-pending-fix`
- scenarios: 14; all matched: **True**

| scenario | task | expected pass | actual pass | matched | stop rejections | guard rejections | writes |
|---|---|---:|---:|---:|---:|---:|---|
| profile_normal | profile | True | True | True | 0 | 0 | `{"profile": 1}` |
| post_normal | post | True | True | True | 0 | 0 | `{"post": 1}` |
| reply_normal | reply | True | True | True | 0 | 0 | `{"reply": 1}` |
| subscribe_normal | subscribe | True | True | True | 0 | 0 | `{"subscribe": 1}` |
| vote_normal | vote | True | True | True | 0 | 0 | `{"vote": 1}` |
| vote_unknown_no_resend | vote | True | True | True | 0 | 0 | `{"vote": 1}` |
| cart_normal | cart | True | True | True | 0 | 0 | `{"cart": 1}` |
| checkout_normal | checkout | True | True | True | 0 | 0 | `{"cart": 1, "checkout": 1}` |
| profile_no_effect_recovery | profile | True | True | True | 0 | 0 | `{"profile": 1}` |
| profile_append_repair | profile | True | True | True | 0 | 0 | `{"profile": 2}` |
| profile_unknown_no_resend | profile | True | True | True | 0 | 1 | `{"profile": 1}` |
| checkout_unknown_no_resend | checkout | True | True | True | 0 | 0 | `{"cart": 1, "checkout": 1}` |
| profile_post_partial | profile_post | True | True | True | 0 | 0 | `{"profile": 1, "post": 1}` |
| profile_premature_stop | profile | True | True | True | 1 | 0 | `{"profile": 1}` |

The grade is computed by `m2_grading.grade` from actual fixture state and the
original task; Runtime `goal_checks` are stored as advisory only.
