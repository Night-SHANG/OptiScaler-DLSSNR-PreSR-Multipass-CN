# Pre-SR CN local maintenance audit — 2026-10-31

## Source boundaries

- Maintenance baseline: `6de9e17` on `Night-SHANG/OptiScaler-DLSSNR-PreSR-Multipass-CN`.
- Development: `wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass` main = `6125a75b37f7e2a408e31934f4827e5660429203` = `v0.8.10`. GitHub release is **prerelease**.
- Stable: `v0.8.3` = `47e134cbcd9d3653d63f58a36d38281e827007ec`; no stable promotion or published-release tracking change.
- Only overlay/catalog/tooling changes are prepared. No F5/Dagherbou functionality imported. No push, workflow dispatch, release, user-local-computer access or external upload.

## Coverage is not just pending=0

- Development catalog: 1,063 active strings; 0 missing/stale, including 758 machine-translated entries. Stable: 1,011 active; 0 missing/stale, including 690 machine-translated entries. These counts include preexisting machine translations; they do not mean human-reviewed or game-tested coverage.
- 140 newly added UI translations; every preexisting translation entry remains byte-for-byte equivalent as parsed JSON. New AI translations remain `machine_translated`.
- Reviewed memory gains only the previously reviewed exact-source `Unlock up to 10 passes`; no AI entries are falsely promoted.
- Fixed moved MenuControls helper scopes; direct-directory C string arrays; pipeline label struct initializers; deferred format labels; constexpr localized arrays; NUL-delimited combo choices; conditional help/tooltip/toast text; adjacent C++ literals; aggregate notification content; dynamic tooltip wrappers after literal instrumentation.
- Independent producer audit: 117 development / 81 stable static status sources, none missing. 13 / 7 dynamic compositions manually matched to exact enumerated variants or bounded templates. `status.zh-CN.json` has 237 exact/template rows.
- Status localization is applied only at menu display boundaries. Stored renderer state, comparisons and logs stay English. API names, IDs, numeric values, paths and runtime error payloads remain unchanged. Unknown future/vendor text falls back to English, deliberately.
- Intentional exclusions: `##`-only ImGui IDs; API/product/DLL names; internal logs and shader/engine identifiers; arbitrary user data and unknown external runtime error payloads. See scanner-rules and status audit JSON for boundaries.

## Local verification

- Python compileall and 100 unit tests pass, including new red/green regression fixtures.
- Strict dual-channel localization check passes; reviewed memory consistency passes; git diff whitespace check passes.
- Generated string headers and actual status resource matcher compiled/run with g++ C++20, `-Wall -Wextra -Werror`.
- Status tests: exact translation priority, source-hash validation, original parameters/error code/path bytes, UTF-8 and braces, empty parameter rejection, delimiter collision fallback, 100,000-character value, adjacent placeholder rejection, placeholder mismatch fallback, unknown English fallback, actual `Loc::DS` timing-suffix composition, display pointer lifetime confined to the ImGui call expression.
- Clean source integration succeeded: development 1,034 literal UI arguments, stable 982; display-status wrappers are additional. Results are in master-integration.log and stable-integration.log. UI scan and separate status source audits are retained alongside this document.

## Not claimed

- No Windows/MSVC Release DLL build, package/hybrid-asset verification, rendered font/UI inspection, or live GPU/game validation was available in this Linux workspace. g++ helper tests are not a substitute for those gates.
- Do not publish on the strength of Python/catalog coverage alone.

## Remote safety

Maintenance-branch push does not match the existing main/master push triggers. A PR runs read-only build/localization-check workflows. Merging/pushing changes to main can trigger build, upstream-sync and release publication through existing workflows. Triggers/permissions were not weakened or modified; parent must separately authorize remote actions and publication.

## Independent review — 2026-10-31

- Reviewed frozen producer commit `6c04e71dbf69033c3c75fa298a8bc514c221cfc1` independently; first run reproduced all 100 passing tests, including the real generated status-resource / extracted `Loc::DS` C++20 compile-and-execute test.
- Found one additional visible-text omission outside the status catalog: deferred sliders construct `std::string("Reset##") + label` in development `DlssNr_MenuControls.cpp` and stable `DlssNr_MenuModel.cpp`. The scanner never sees the final SmallButton text. A narrowly filename-scoped display-prefix patch now uses existing `TL("Reset")`, retaining `"##" + label` unchanged. The regression first failed on the original code, then passed; it checks both channel filenames, idempotency, and no modification to an Engine.cpp fixture.
- Independent strict resources: development 1,063 / stable 1,011, zero missing/stale; reviewed translation memory synchronized (403 sources); Python compilation and whitespace checks pass. All 101 unit tests pass after the repair.
- Independent status-source audit reproduced development 117 static / 13 dynamic and stable 81 static / 7 dynamic, with no missing known static sources. Runtime parameters are copied unchanged and unknown strings fall back; exact matches precede templates. Status `.c_str()` temporaries are confined to synchronous ImGui call full-expressions, not stored pointers. Pipeline runtime label arrays are no longer constexpr. Scoped label comparisons use the same localized labels as callers; technical IDs and combo NUL boundaries were inspected.
- Independently compared 78 development and 73 stable non-menu DLSS-NR shader/backend source files against their frozen git objects: all byte-identical after integration. This is stronger than checking only the status patch's fixture.
- Remaining gate: Windows/MSVC build, actual font rendering, and live GPU/game execution have **not** been performed by this reviewer. This audit does not assert universal future-string coverage or production runtime validation.
- Post-repair full clean git-archive integration rerun: development 1,034 / stable 982 literal arguments. Comparing complete before/after generated trees shows exactly one changed source line per channel, the intended Reset prefix; no other generated source/resource changed. Both ordinary generated Strings headers separately compiled/executed with g++ C++20 `-Wall -Wextra -Werror`.
