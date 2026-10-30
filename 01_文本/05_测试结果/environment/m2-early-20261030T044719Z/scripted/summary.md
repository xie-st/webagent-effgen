# M2 scripted local fault check

- decision source: `scripted_browser_no_model`; model calls: 0
- scenarios: 10; all matched: **False**

| scenario | task | expected pass | actual pass | matched | writes |
|---|---|---:|---:|---:|---|
| normal_profile | profile | True | True | True | `{"profile": 1}` |
| normal_checkout | checkout | True | True | True | `{"cart": 1, "checkout": 1}` |
| no_effect_recovery | profile | True | True | True | `{"profile": 1}` |
| append_correction | profile | True | True | True | `{"profile": 2}` |
| unknown_profile | profile | True | True | True | `{"profile": 1}` |
| unknown_checkout | checkout | True | True | True | `{"cart": 1, "checkout": 1}` |
| partial_profile_post | profile_post | True | True | True | `{"profile": 1, "post": 1}` |
| missing_subscribe_vote | subscribe_vote | False | False | False | `{}` |
| duplicate_vote | vote | False | False | True | `{"vote": 2}` |
| missing_checkout | checkout | False | False | True | `{"cart": 1}` |

This is a scripted browser environment check, not a model acceptance or an official score.
