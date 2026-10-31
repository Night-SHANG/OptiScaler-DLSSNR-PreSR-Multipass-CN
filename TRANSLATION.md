# Translation maintenance

## Resource model

The localization pipeline keeps two persisted source inventories and one shared Chinese store:

- `master/catalog.json`, `master/en-US.json`, `master/pending.json`: current upstream `main` (the channel directory retains the shared name `master`).
- `stable/catalog.json`, `stable/en-US.json`, `stable/pending.json`: current latest stable tag.
- `zh-CN.json`: shared translations tied to the exact English `source_hash`.
- `translation-memory.zh-CN.json`: reviewed exact-source translations used to seed either channel.
- `glossary.json`: stable product terminology supplied to optional machine translation.

The same English source receives the same deterministic key in both channels. If upstream wording changes, the new wording receives a new key; the older stable wording and translation remain valid instead of being overwritten.

## States

A valid live Chinese entry has one of these states:

- `reviewed`: human-confirmed. Automation must never overwrite `text`.
- `machine_translated`: generated candidate accepted for runtime use but still reviewable.

Missing or stale translations use English at runtime. A reviewed entry whose upstream English changes remains preserved with its old source hash; an automatic translator may write a separate `candidate`, but it may not replace the reviewed text.

Example:

```json
{
  "ui.auto.abcd1234": {
    "text": "启用帧生成",
    "state": "reviewed",
    "source_hash": "..."
  }
}
```

## Incremental scanning

Run:

```bash
python tools/scan_ui.py --source _upstream --channel master --update --report reports/master-localization-scan.md
python tools/scan_ui.py --source _stable --channel stable --update --report reports/stable-localization-scan.md
```

Keys are immutable and derived from the exact English source. Exact existing sources retain their key. A highly similar replacement in the same UI scope is reported as a changed string, but receives a new source-derived key so master and stable can safely keep different wording at the same time. Removed catalog entries stay marked obsolete so translation history is not silently destroyed.

## Validation rules

`python tools/check_localization.py --channel all` verifies both persisted inventories:

- catalog/source hashes;
- `en-US` parity;
- allowed translation states;
- printf placeholders (`%s`, `%.2f`, etc.);
- `std::format` placeholders (`{0}`, `{name:...}`);
- exact preservation of ImGui `##hidden-id` suffixes.

A missing translation is not a build error: English fallback is required behavior. A structurally invalid translation is a build error.

## Glossary

Use the maintained terminology in `Localization/glossary.json`. Examples:

- Frame Generation → 帧生成
- Upscaling → 超分辨率
- Ray Reconstruction → 光线重建
- Balanced → 均衡
- Ultra Performance → 超级性能

Do not translate product/API/protocol/file names such as `DLSS`, `FSR`, `XeSS`, `DirectX`, `Vulkan`, DLL names or C++ identifiers. They can remain inside an otherwise translated sentence.

## Optional automatic translation

Set these GitHub Actions Secrets only if incremental machine translation is wanted:

- `TRANSLATION_API_URL`: an OpenAI-compatible Chat Completions endpoint URL.
- `TRANSLATION_API_KEY`
- `TRANSLATION_MODEL`

Then run:

```bash
python tools/translate_missing.py
```

The tool sends only current missing/changed source strings plus the glossary. It never sends the whole language pack for retranslation and never overwrites a `reviewed` translation. Secrets are read only from environment variables and are never written to the repository.

Without these secrets, the command exits successfully, keeps entries in each channel's `pending.json`, and runtime falls back to English.

## Reviewing a changed string

When a source changes, inspect the matching channel `pending.json` and any generated `candidate`. After confirming the new wording, set `text` to the approved translation, set `source_hash` to the new hash from `pending.json`, set `state` to `reviewed`, then run:

```bash
python tools/update_translation_memory.py
python tools/check_localization.py --strict
```

The first command updates only fresh `reviewed` entries in translation memory. Machine-translated entries never enter the reviewed memory automatically.

## Fork-specific UI

扫描范围包含 `OptiScaler/dlssnr/**`。普通 OptiScaler 文本复用共享中文；wilsjo2/OptiScaler-DLSSNR-PreSR-Multipass 新增文本只在首次发现或源文变化时进入待翻译列表。

## Pre-SR v0.8.10 UI coverage

The controls now live in `DlssNr_MenuControls.cpp`. Scoped rules cover the moved sliders, checkbox helpers, model arrays, deferred `std::format` pass labels (rewritten through `Loc::F`), conditional help text and NUL-separated combo choices. The validator preserves combo item separators as well as placeholders and hidden IDs. AI-authored additions remain `machine_translated`; they do not replace reviewed translations or enter reviewed translation memory automatically.

### Display-only status text

`Localization/status.zh-CN.json` contains exact known renderer status messages and narrowly bounded templates. `StatusLocalization.h` translates only the displayed copy, invoked through `Loc::DS` at audited NR menu call sites. The renderer's stored English status, equality checks, logs, error payloads, paths and technical IDs are not rewritten. Template parameters remain byte-for-byte unchanged; unknown messages fall back to English. Denoise timing suffixes are translated only when both the base status and suffix are recognized.

Run `python tools/audit_status_sources.py --source _upstream --out reports/master-status-audit.json` (and the stable source equivalent) to check newly added static producer messages and review dynamic compositions. The audit is deliberately separate from the ordinary UI catalog so `pending=0` cannot hide opaque `%s` diagnostic sources. Tests compile and run the pure C++ status matcher where a portable compiler is available; a Windows build and GPU/game validation remain separate requirements.
