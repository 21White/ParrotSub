# Changelog · 更新日志

All notable changes to **ParrotSub** are documented here.
本文档记录 **ParrotSub** 的全部公开变更。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
本文档遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式，并采用
[语义化版本](https://semver.org/lang/zh-CN/spec/v2.0.0.html)。

> **Version policy** · **版本策略**
>
> - `MAJOR` (x.0.0) – breaking changes / 不向后兼容的破坏性改动
> - `MINOR` (0.x.0) – new user-facing features / 新功能
> - `PATCH` (0.0.x) – bug fixes & docs / 缺陷修复与文档更新

## [Unreleased]
### Added
-

### Changed
-

### Fixed
-

---

## [0.4.0] – 2026-05-15

### Added
- **Translation language pickers** – the *Translate From* / *Translate
  To* fields on the Settings page are now dropdown menus instead of
  free-text inputs. Each option shows the language's endonym plus its
  ISO code (e.g. `中文 (zh)`, `日本語 (ja)`).
  Settings 页面的 *Translate From / Translate To* 改为下拉菜单，每一项
  以「原文名 + ISO 代码」展示（例如 `中文 (zh)`、`日本語 (ja)`）。
- **Smart source-language list** – choices are the intersection of
  Whisper-recognisable languages and argos-translate language packages
  (≈43 source languages / 47 target languages). When a `*.en-mlx`
  English-only Whisper model is selected, the source dropdown
  automatically locks to English.
  源语言列表是 Whisper 识别语言与 argos-translate 翻译语言的交集
  （约 43 种源语言 / 47 种目标语言）。一旦选了 `*.en-mlx` 这种仅英文
  的 Whisper 模型，源语言会自动锁死为 English。
- New `parrotsub.languages` module: language-name lookup, the curated
  Whisper × argos lists and the helper functions used by the Settings
  page.
  新增 `parrotsub.languages` 模块：语言名查找、Whisper × argos 取交
  的列表，以及 Settings 页面用到的辅助函数。

### Changed
- Home page's *Translation* card description now shows the source /
  target language by their friendly endonym name instead of the raw
  ISO code (e.g. `日本語 → 中文 · offline (argos-translate)`).
  Home 页面 *Translation* 卡片描述改为按语言原名展示源/目标语言，
  不再显示纯 ISO 代码（例如 `日本語 → 中文 · 离线翻译（argos-translate）`）。

### Removed
- **Online translation toggle** – the *OnlineTranslation* setting is
  no longer surfaced in the UI; it stays in the backend config and is
  force-written to `false` on every save. Online translation is parked
  and will return in a future release.
  移除 UI 中的 *OnlineTranslation* 开关；该字段在后端配置中保留，
  每次保存都会被强制写为 `false`。在线翻译功能将在后续版本回归。

---

## [0.3.0] – 2026-05-15

### Added
- **Bilingual UI (English / 中文)** – ships a complete English/Chinese
  message catalogue under `parrotsub.i18n`, covering the sidebar
  tooltips, status pill, Tasks / Settings / Exports pages and every
  per-field label on the Settings page.
  新增中英双语 UI，在 `parrotsub.i18n` 内置完整的中英文词条，覆盖
  侧边栏 Tooltip、状态胶囊、Tasks / Settings / Exports 三个页面以及
  Settings 页所有字段标签。
- **Language toggle** – a *languages* icon button in the sidebar flips
  between locales at runtime; every visible string re-translates
  immediately via `Translator.locale_changed`.
  侧边栏新增 *languages* 图标按钮，运行时一键切换语言，所有可见
  文字会立即通过 `Translator.locale_changed` 信号实时翻译。
- **Persistent UI preferences** – new `parrotsub.ui_config` module
  saves the chosen theme + locale to
  `~/.config/parrotsub/parrotsub.config`, kept separate from the
  upstream realtime_subtitle backend config so the two never collide.
  新增 `parrotsub.ui_config` 模块，把主题和语言保存到
  `~/.config/parrotsub/parrotsub.config`，与上游 `realtime_subtitle`
  后端的配置完全分离。
- **OS-aware default locale** – on first launch ParrotSub auto-picks
  Chinese on macOS systems whose `locale.getlocale()` reports `zh_*`,
  otherwise English.
  首次启动自动跟随系统：macOS `locale.getlocale()` 返回 `zh_*` 时
  默认中文，否则默认英文。

### Changed
- Status pill messages now route through `t()` and translate live;
  also surfaces `Language: …` / `Theme: …` / `Settings saved`
  acknowledgements after user actions.
  状态胶囊文字改为走 `t()`，并在切换语言/主题与保存设置后给出
  本地化反馈。

---

## [0.2.0] – 2026-05-15

### Added
- **Initial public release** of ParrotSub – a modern desktop UI for
  realtime offline speech-to-subtitle on Apple Silicon Macs.
  ParrotSub 首个公开版本，面向 Apple Silicon Mac 的现代化离线
  实时语音转字幕桌面应用。
- **Sidebar + header app shell** – 56 px icon rail (Tasks / Settings /
  Exports), 57 px header with title, version and a live status pill.
  侧边栏 + 顶部 Header 应用框架（56px 图标导航条 + 57px 顶部栏 +
  实时状态胶囊）。
- **shadcn-style theming** with light & dark palettes, built on a
  bespoke set of QSS design tokens. Teal brand accent
  (`#0d9488` light / `#14b8a6` dark) leads every primary action
  and active state.
  shadcn 风格主题，基于一套 QSS 设计 token 实现明暗双色板，
  以 teal 为品牌主色，所有主操作与激活态都用它。
- **Tasks page** – Start / Stop recording, dual *Original* and
  *Translation* cards that update live, on/off switches for two
  always-on-top floating overlays, one-click export.
  Tasks 页面：开始 / 停止录音、原文 / 译文双卡片实时刷新、两个
  置顶悬浮窗的独立开关、一键导出。
- **Settings page** – every backend config field surfaced into 6
  cards (Audio Input · Whisper Model · Translation · Subtitle
  Layout · Floating Window · Speaker Recognition & Storage).
  Save / Reset buttons, type-aware inputs.
  Settings 页面：把后端的所有配置字段拆成 6 张卡片，按字段类型
  自动生成下拉、开关或文本框，含保存与重置。
- **Exports page** – browse every saved session, see what artefacts
  exist, double-click to open in Finder.
  Exports 页面：浏览所有导出会话，标注产物类型，双击直接在 Finder
  中打开。
- **Frameless floating overlays** with rounded corners, translucent
  background, on-top, mouse-drag relocation, outline-text rendering.
  无边框圆角悬浮字幕窗，半透明、置顶、可鼠标拖动、文字带描边。
- **Vendored offline backend** – ships
  [`realtime_subtitle`](https://github.com/caoqiming/realtime-subtitle)
  (mlx-whisper + argos-translate + speechbrain + PyAudio) inside
  `src/realtime_subtitle/`, so installing ParrotSub gives a
  self-contained working app with no external Python package.
  内嵌
  [`realtime_subtitle`](https://github.com/caoqiming/realtime-subtitle)
  离线后端到 `src/realtime_subtitle/`，单独 `pip install` ParrotSub
  即可获得自包含的可用应用，不依赖外部 PyPI 同名包。
- **Two CLIs** – `parrotsub` (default UI) and the legacy
  `realtime-subtitle` entry point for backward compatibility.
  两个 CLI：`parrotsub`（默认 UI）与 `realtime-subtitle`（兼容旧
  脚本的入口）。

### Changed
- Pinned `speechbrain>=1.1.0` instead of the upstream `==1.0.3`,
  fixing a startup crash on `torchaudio>=2.9` (the upstream version
  uses the removed `torchaudio.list_audio_backends()` API).
  把 `speechbrain` 钉到 `>=1.1.0`，修复上游 `==1.0.3` 在
  `torchaudio>=2.9` 下因 `torchaudio.list_audio_backends()` 被移除
  导致的启动崩溃。

### License
- Released under **Apache License 2.0**. The vendored backend
  retains its original **MIT License** (Copyright © 2025 glimmer);
  the upstream license text is preserved in
  `THIRD_PARTY_LICENSES/realtime-subtitle.LICENSE`.
  采用 **Apache License 2.0** 发布。内嵌的后端继续沿用原作者的
  **MIT 许可证**（版权所有 © 2025 glimmer），上游许可文本保留在
  `THIRD_PARTY_LICENSES/realtime-subtitle.LICENSE`。

[Unreleased]: https://github.com/21White/ParrotSub/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/21White/ParrotSub/releases/tag/v0.4.0
[0.3.0]: https://github.com/21White/ParrotSub/releases/tag/v0.3.0
[0.2.0]: https://github.com/21White/ParrotSub/releases/tag/v0.2.0
