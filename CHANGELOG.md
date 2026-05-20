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

## [0.7.0] – 2026-05-20

### Changed
- **Model download stack rewritten end-to-end, SmartSub-style.**
  Inspired by `SmartSub/main/helpers/modelDownloader.ts`, we now do
  the network ourselves via `requests` instead of going through
  `huggingface_hub.snapshot_download`. The new pipeline:

  1. Hits the HF JSON API (`/api/models/{repo}` then
     `/api/models/{repo}/tree/{rev}`) to learn the revision SHA, the
     list of files, each file's size, and each file's git/LFS blob
     OID. Two hops because the model-info endpoint doesn't expose
     file sizes and the tree endpoint doesn't expose the revision
     SHA.
  2. Downloads each file with raw `requests.get(stream=True,
     timeout=(30, 60))` — a 30-second connect timeout and a
     60-second **inactivity timeout** (no bytes for 60 s → abort and
     try the next endpoint). Sends `Range: bytes=N-` so an
     interrupted transfer resumes from where the last try stopped,
     even across endpoints and across application restarts.
  3. Writes into the standard HuggingFace cache layout
     (`models--<org>--<repo>/blobs/<oid>` + `snapshots/<rev>/<file>`
     symlinks + `refs/main`) so `mlx_whisper` loads from the same
     cache without ever needing to re-fetch.
  4. Emits a new `progress(repo_id, done, total, speed_bps, eta_s)`
     signal **on every chunk** (not just every 500 ms), so the
     header status pill can render
     `Downloading {model}: 37% (614/1638 MB · 5.2 MB/s · ETA 03:18)`.
  5. Logs every attempt and every per-endpoint failure to stderr
     under the `[parrotsub.download]` prefix, including the file
     name, the resume offset, the exception type and the message,
     so debugging takes 10 seconds instead of an hour.

  模型下载实现完全重写，照搬 SmartSub `modelDownloader.ts` 的思路。
  改为直接用 `requests` 自己做网络，不再走 `huggingface_hub.
  snapshot_download`。新管线：

  1. 通过 HF JSON API（先 `/api/models/{repo}` 拿 revision SHA，再
     `/api/models/{repo}/tree/{rev}` 拿文件列表 + size + blob OID）。
  2. 每个文件用 `requests.get(stream=True, timeout=(30, 60))` 流
     下载：连接超时 30 秒、单 chunk 阅读超时 60 秒（**60 秒收不到
     字节就主动 abort**），失败自动 fallback 到下一个 endpoint，并
     带 `Range: bytes=N-` 续传——跨 endpoint 跨重启都能从上次断点
     接着下，不会浪费已经下到的字节。
  3. 写入标准 HuggingFace 缓存结构（`models--<org>--<repo>/
     blobs/<oid>` + `snapshots/<rev>/<file>` 软链 + `refs/main`），
     `mlx_whisper` 加载时直接命中缓存。
  4. `progress(repo_id, done, total, speed_bps, eta_s)` 信号每个
     chunk 都发，顶栏胶囊实时显示
     `正在下载 {model}：37%（614/1638 MB · 5.2 MB/s · 剩余 03:18）`。
  5. 每次尝试 / 每次失败都用 `[parrotsub.download]` 前缀打到
     stderr，含文件名、断点续传偏移、异常类型、错误消息——出问题
     调试时 10 秒钟就能定位。

### Added
- New module `parrotsub.downloader` exposing `download_repo()`,
  `DownloadProgress`, `DownloadAbortedError`, `DownloadFailedError`.
  Tunables (`INACTIVITY_TIMEOUT`, `CONNECT_TIMEOUT`, `CHUNK_SIZE`)
  live at module scope so they're easy to find and change.
  新增 `parrotsub.downloader` 模块，导出 `download_repo()`、
  `DownloadProgress`、`DownloadAbortedError`、`DownloadFailedError`。
  所有阈值（INACTIVITY_TIMEOUT / CONNECT_TIMEOUT / CHUNK_SIZE）
  集中在模块顶端，想改就能改。
- Status-pill download line now includes speed and ETA — e.g.
  `Downloading whisper-large-v3-turbo: 37% (614/1638 MB · 5.2 MB/s
  · ETA 03:18)` / 中文版同步加 `5.2 MB/s · 剩余 03:18`. Helpers
  `_human_speed` and `_human_duration` keep formatting consistent.
  顶栏下载提示新增速度和剩余时间。新增 `_human_speed` /
  `_human_duration` 两个辅助函数统一格式。

### Removed
- The `_make_progress_tqdm` factory and its `tqdm`-shimming
  machinery introduced in v0.6.5. The new downloader emits byte
  counts directly so the indirection is no longer needed.
  v0.6.5 引入的 `_make_progress_tqdm` 工厂以及 tqdm shim 全部移除。
  新下载器直接发字节计数，不再需要这一层间接。

---

## [0.6.5] – 2026-05-19

### Added
- **Live download progress in the header status pill.** Before this
  release, clicking *Download* on a model showed
  `Downloading {model} via {endpoint}…` and then sat there silently
  for minutes while a big file streamed through a slow mirror. Users
  reasonably concluded the download was hung and gave up — but the
  download was actually working, just slow (hf-mirror.com routinely
  takes 2–10 minutes for ≥500 MB files). The pill now updates
  ~2 times per second with `Downloading {model}: 37% (614/1638 MB)` /
  `正在下载 {model}：37%（614/1638 MB）` so you can see it's
  progressing.
  顶栏状态胶囊新增实时下载进度。之前点 *Download* 之后会一直显示
  `正在从 {endpoint} 下载 {model}…` 几分钟不动，用户合理地以为卡死
  就放弃了——其实下载在跑，只是 hf-mirror.com 大文件慢（500 MB+
  常常要 2–10 分钟）。现在胶囊每秒 ~2 次刷新成
  `正在下载 {model}：37%（614/1638 MB）`，肉眼看得见在动。

### Changed
- `ModelDownloadWorker` exposes a new `progress(repo_id, done_bytes,
  total_bytes)` signal in addition to the existing
  `attempting` / `downloaded` signals. Aggregates byte counts across
  all live per-file `tqdm` bars while `snapshot_download`'s thread
  pool runs.
  `ModelDownloadWorker` 在原有 `attempting` / `downloaded` 之外新增
  `progress(repo_id, done_bytes, total_bytes)` 信号，把
  `snapshot_download` 线程池里同时跑的多个 per-file tqdm 字节数
  累加后发出来。
- New private factory `parrotsub.models._make_progress_tqdm(worker)`
  returns a `tqdm` subclass bound to that worker's `progress`
  signal. It only tracks `unit='B'` bars (per-file byte progress) so
  the noisy "Fetching N files" outer bar doesn't pollute totals, and
  throttles emits to ~one every 500 ms so the UI thread isn't
  swamped.
  新增内部工厂 `parrotsub.models._make_progress_tqdm(worker)`，返回
  绑到该 worker `progress` 信号的 `tqdm` 子类。它只跟踪 `unit='B'`
  的字节进度条（避免被外层"Fetching N files"误算），并把发射节流
  到 ~500 ms 一次以防止挤爆 UI 事件循环。

### Fixed
- The Settings page now connects the new `progress` signal in
  `_on_download_model_clicked` and renders it via a new
  `_on_model_download_progress` slot, replacing the static
  *Downloading via…* message with the live percentage line.
  Settings 页面在 `_on_download_model_clicked` 里连接新信号，slot
  `_on_model_download_progress` 实时刷新百分比，取代之前那条不动
  的 *Downloading via…* 文案。

---

## [0.6.4] – 2026-05-19

### Fixed
- **Model downloads no longer hang forever on big files.** Root cause:
  `huggingface_hub.snapshot_download` has **no** per-transfer timeout
  by default, so when the China mirror started streaming a multi-GB
  weights file and then stalled part-way, the worker thread waited
  silently forever, the `attempting` signal never fired again, the
  endpoint-chain fallback never kicked in, and the user just saw a
  parked `Fetching 4 files: 0%` progress bar. ParrotSub now sets
  `HF_HUB_DOWNLOAD_TIMEOUT=60` at launch (idempotent – the user's
  explicit override always wins). Combined with `etag_timeout=15` on
  the metadata HEAD call, a stalled mirror now fails fast and the
  fallback to `https://huggingface.co` actually triggers.
  模型下载不再因大文件假死。根因：`huggingface_hub.snapshot_download`
  默认**没有**单次传输超时，hf-mirror 在传几 GB 权重文件时常常卡到
  几十兆就停，worker 线程会无声无息等到天荒地老，endpoint 链回退
  根本触发不了，用户看到的就是 `Fetching 4 files: 0%` 永远不动。
  ParrotSub 现在在启动时设置 `HF_HUB_DOWNLOAD_TIMEOUT=60`（用户显式
  覆盖优先），配合 `etag_timeout=15`，卡住的镜像会快速失败，正确
  fallback 到 `https://huggingface.co`。
- **`is_model_installed()` is now actually strict.** Previously it
  returned `True` as soon as `config.json` was in the cache, which
  was misleading after an interrupted download (metadata fetched +
  weights missing or half-fetched both look "installed"). The check
  now requires:
  1. `config.json` is present,
  2. the snapshot directory has at least one weights file
     (`*.safetensors` / `*.npz` / `*.bin` / `*.gguf`),
  3. there are no `.incomplete` blobs in the `blobs/` directory.
  Otherwise the `⬇` badge stays on the model in the dropdown.
  `is_model_installed()` 现在做的是**真严格**的判断：之前只看
  `config.json` 在不在，半下载（拿到了元数据但权重没下完）也会被
  误判成已安装。现在必须同时满足 3 个条件：(1) `config.json` 在；
  (2) snapshot 目录里至少有一个权重文件（`*.safetensors` /
  `*.npz` / `*.bin` / `*.gguf`）；(3) `blobs/` 目录里没有
  `.incomplete` 残留。否则下拉框继续显示 `⬇`。

### Added
- `parrotsub.models.has_incomplete_download(repo_id)` and
  `cleanup_incomplete_downloads(repo_id)` helpers. The downloader
  invokes the cleanup on every failed attempt so the next endpoint
  starts from a clean slate; the Settings page invokes it before the
  first attempt too.
  新增 `has_incomplete_download(repo_id)` / `cleanup_incomplete_
  downloads(repo_id)` 工具函数。下载 worker 每次失败都会清理一次，
  让下一个 endpoint 从干净状态开始；Settings 页面在点 Download 前
  也会先清一次。
- `parrotsub.models.ensure_default_download_timeout()` (sets
  `HF_HUB_DOWNLOAD_TIMEOUT=60` if unset). Called by `app.launch()`.
  新增 `ensure_default_download_timeout()` 帮助函数，启动时调一次。
- The downloader now prints each attempt + each failure to `stderr`,
  prefixed with `[parrotsub.download]`, so terminal output makes it
  obvious which mirror was tried and why it failed.
  下载 worker 现在把每次尝试 / 每次失败都打到 stderr（前缀
  `[parrotsub.download]`），终端上一眼就能看出走了哪个镜像、为什么
  失败。

---

## [0.6.3] – 2026-05-19

### Changed
- **Model download tries multiple HuggingFace endpoints in turn**, so
  a flaky mirror doesn't have to mean "download failed". The order is:
  1. whatever `HF_ENDPOINT` currently resolves to (the user's
     explicit choice, or our `https://hf-mirror.com` default);
  2. `https://hf-mirror.com` (skipped if it was first);
  3. `https://huggingface.co` (the official one, always last).
  The header status pill now shows `Downloading {model} via
  {endpoint}…` / `正在从 {endpoint} 下载 {model}…` so you can see
  which mirror is being attempted at any moment.
  模型下载现在会**按顺序尝试多个 HuggingFace 镜像**，单一镜像抽风
  不再等于"下载失败"。顺序：(1) 当前 `HF_ENDPOINT`（你的显式设置
  或我们的默认 `https://hf-mirror.com`）→ (2) `hf-mirror.com`（若
  与第 1 个重复则跳过）→ (3) 官方 `https://huggingface.co` 兜底。
  顶栏状态胶囊会实时显示 `正在从 {endpoint} 下载 {model}…`，让你
  随时知道当下走的是哪个源。

### Added
- `parrotsub.models.FALLBACK_DOWNLOAD_ENDPOINTS` – the ordered tuple
  of fallback endpoints used by the downloader.
  `ModelDownloadWorker` also gains an `attempting(repo_id, endpoint)`
  signal so the Settings page can keep the UI in sync.
  新增 `parrotsub.models.FALLBACK_DOWNLOAD_ENDPOINTS` 常量；
  `ModelDownloadWorker` 新增 `attempting` 信号，让 Settings 页能
  实时反馈当前正在试哪个镜像。
- New i18n key `settings.model.downloading_via` (EN + ZH).
  新增 EN + ZH 词条 `settings.model.downloading_via`。

---

## [0.6.2] – 2026-05-19

### Changed
- **Header status pill is quieter when a fallback model kicks in.**
  Replaces the long-winded
  `Using {fallback} (download {selected} from Settings → Whisper Model)`
  with a single short `Using {fallback}` / `正在使用 {fallback}`, and
  switches its colour from "warn" (amber) to "active" (teal) since
  it's just an informational status, not a problem.
  顶栏状态胶囊的 fallback 提示精简为只显示 `正在使用 {fallback}`，
  去掉了"去 Settings → Whisper Model 下载 …" 那一长串说明；色调也
  从警示橙改为品牌青，更像状态汇报而不是警告。
- The "no whisper model" message is similarly shortened to
  `No whisper model downloaded` / `未下载任何 Whisper 模型`.
  "未下载任何模型" 那条提示也跟着精简成一句话。

---

## [0.6.1] – 2026-05-19

### Fixed
- **App no longer crashes at launch when the saved Whisper model isn't
  downloaded.** Reported failure: `./start.sh` aborted with
  `huggingface_hub.errors.FileMetadataError /
  LocalEntryNotFoundError` because the upstream backend's warm-up call
  `mlx_whisper.transcribe(np.zeros(1024), …)` tried to silently
  download the configured model (e.g. `whisper-large-v3-turbo`) via
  the HF mirror, which can fail on flaky networks.
  应用启动崩溃已修复。报错路径：`./start.sh` 因上游后端的
  `mlx_whisper.transcribe(np.zeros(1024), …)` 预热调用试图通过
  huggingface_hub 静默下载用户配置中的模型（例如
  `whisper-large-v3-turbo`），网络一卡就抛
  `FileMetadataError / LocalEntryNotFoundError` 导致整个应用退出。

### Changed
- **Startup never auto-downloads a model anymore.** If the saved
  `ModelName` isn't in the HuggingFace cache, ParrotSub now picks an
  already-installed model from `AllModelName` (preferring
  `whisper-tiny.en-mlx`) and uses it **for this session only** so the
  warm-up loads instantly from disk. The saved config is left
  untouched, so the Settings page still shows the user's actual
  preference with the `⬇` badge and they can download it at their own
  pace. The header status pill shows
  `Using {fallback} (download {selected} from Settings → Whisper Model)`.
  启动不再触发任何自动下载。若 `ModelName` 配置的模型不在 HuggingFace
  缓存里，ParrotSub 会从 `AllModelName` 里找一个已下载的模型（优先
  `whisper-tiny.en-mlx`）作为本次会话的临时替代，配置文件原样保留——
  Settings 页面仍然显示用户选的模型并标 `⬇`，可以从那里主动点
  Download。顶栏状态胶囊会提示
  `正在使用 {fallback}（去 Settings → Whisper Model 下载 {selected}）`。
- **Defense in depth in the vendored backend.** Both the warm-up call
  in `RealtimeSubtitle.__init__` and every per-segment
  `mlx_whisper.transcribe` call in the handler loop are now wrapped in
  `try/except`. A whisper failure prints a clear warning once,
  surfaces a status message, and never tears the app or worker thread
  down.
  内嵌后端加双保险：`RealtimeSubtitle.__init__` 的预热调用与 handle
  循环里的每次 `mlx_whisper.transcribe` 都包了 try/except，模型异常
  只打一次清晰的 warning，绝不再把应用或后台线程拖垮。

### Added
- `parrotsub.models.find_installed_model(cfg)` – returns the first
  whisper model that's already in the local HF cache, falling back to
  `whisper-tiny.en-mlx` as a last resort. Used by `app.launch()` for
  the no-download fallback above.
  新增 `parrotsub.models.find_installed_model(cfg)`：返回 HF 缓存中已
  存在的第一个 whisper 模型，最后兜底到 `whisper-tiny.en-mlx`。`app.
  launch()` 用它实现上面那个"不下载"的 fallback。
- New i18n keys `status.model_fallback` and `status.no_model` (EN +
  ZH) for the header status pill messages above.
  新增 EN + ZH 词条 `status.model_fallback` / `status.no_model`，对应
  上面的状态胶囊文案。

---

## [0.6.0] – 2026-05-19

### Added
- **Whisper model manager in the Settings page.** The *Whisper Model*
  dropdown now shows the install status of every model in
  `AppConfig.AllModelName` as a `✓ / ⬇` badge plus an approximate
  on-disk size (e.g. `✓  mlx-community/whisper-tiny.en-mlx  (~75 MB)`).
  A new *Download* button next to the dropdown pulls the currently
  selected model in the background and flips the badge from ⬇ to ✓
  on completion. Header status pill shows
  `Downloading {model}…` / `Model downloaded: {model}` /
  `Model download failed: {error}`.
  Settings 页面新增 Whisper 模型管理：模型下拉框对每一项显示 `✓ / ⬇`
  徽标加大致体积（例如 `✓ mlx-community/whisper-tiny.en-mlx (~75 MB)`），
  旁边新增 *下载* 按钮可在后台拉取当前选中的模型，完成后徽标自动从
  ⬇ 翻成 ✓。顶栏状态胶囊会反馈 `正在下载 {model}…` / `模型下载完成：
  {model}` / `模型下载失败：{error}`。
- **`parrotsub.models` module.** Centralises:
  - `is_model_installed(repo_id)` – uses HuggingFace's
    `try_to_load_from_cache` so partial downloads are treated as
    "missing".
  - `model_size_label(repo_id)` – cached on-disk approximations for
    each model in `AllModelName`.
  - `ModelDownloadWorker(QThread)` – background download via
    `huggingface_hub.snapshot_download`, emits a `downloaded`
    signal with `(repo_id, success, message)`.
  - `ensure_default_hf_endpoint()` / `active_hf_endpoint()` – set
    `HF_ENDPOINT` to the China mirror (`https://hf-mirror.com`)
    when the user hasn't explicitly chosen one.
  新增 `parrotsub.models` 模块：模型检测、体积估算、后台下载线程、
  国内镜像默认值全部集中管理。

### Changed
- **`HF_ENDPOINT` defaults to `https://hf-mirror.com` on launch**
  when the env var is unset, so model downloads triggered from the
  UI (or by the upstream backend at first load) automatically take
  the China mirror. Set `HF_ENDPOINT` in your shell before launching
  to override. The Settings page shows the active endpoint under
  the model dropdown.
  启动时若未设置 `HF_ENDPOINT`，自动默认为国内镜像
  `https://hf-mirror.com`，UI 触发的模型下载以及上游后端首次加载时
  都走这个镜像。想覆盖直接在 shell 里 `export` 自己的即可。Settings
  页面也会在模型下拉框下方实时显示当前镜像。

---

## [0.5.1] – 2026-05-18

### Changed
- **Subtitle layout defaults retuned for the floating overlay.**
  Fresh installs and the *Settings → Reset to defaults* action now use
  a wider, shorter shape that reads better in the on-top overlays:

  | Field                          | Old | New |
  | ------------------------------ | --- | --- |
  | `SubtitleLength`               | 80  | **90** |
  | `SubtitleHight` (line count)   | 3   | **2**  |
  | `TranslationSubtitleLength`    | 39  | **50** |
  | `TranslationSubtitleHight`     | 3   | **2**  |

  字幕排版的默认值已调优：原文单行从 80 拉宽到 **90**，译文从 39 拉宽
  到 **50**，原文 / 译文的可见行数都从 3 改为 **2**，让悬浮字幕窗
  看起来更紧凑、更易读。仅影响新装环境与 *Settings → Reset to
  defaults*；老用户已经保存过的配置不会被覆盖。

---

## [0.5.0] – 2026-05-15

### Added
- **Clear history button on the Tasks page.** A new outline-style
  button next to *Export* stops the live pipeline if it is still
  running, takes the backend lock, and wipes the in-memory audio
  buffer, every archived/temp segment, and the GUI's thrashing
  counter — leaving both subtitle panes (and any open overlays)
  empty. The header status pill confirms with `History cleared` /
  `历史已清空`.
  Tasks 页面新增 *清空历史* 按钮：在 *Export* 旁边，点击后会先停掉正在
  运行的实时识别（如有），加锁清空音频缓冲与所有已识别的字幕段，并
  重置 GUI 的防抖计数；原文 / 译文窗格和打开着的悬浮窗也会同步清空，
  顶栏状态胶囊提示 `History cleared` / `历史已清空`。

### Changed
- **Floating subtitle overlays now genuinely stay on top across other
  apps.** On macOS the previous `Qt.WindowType.Tool` flag caused the
  overlay to demote to a normal window as soon as ParrotSub itself
  lost focus, which let Safari / Code / Zoom etc. cover the
  subtitles. The flag is gone; the overlay now uses
  `Frameless | WindowStaysOnTopHint` plus the
  `WA_ShowWithoutActivating` attribute so it never steals focus,
  and on macOS we additionally bump the underlying `NSWindow.level`
  to `NSStatusWindowLevel` (25) via pyobjc.
  悬浮字幕窗现在能真正盖在其他应用之上。之前 `Qt.WindowType.Tool` 在
  macOS 上会让 ParrotSub 失焦时悬浮窗降级，导致被 Safari / VSCode /
  Zoom 等应用挡住。现已去掉该标志，改为 `Frameless +
  WindowStaysOnTopHint + WA_ShowWithoutActivating`（不抢焦点），并在
  macOS 上通过 pyobjc 把底层 `NSWindow.level` 提到
  `NSStatusWindowLevel`（25）。
- **`pyobjc-core` / `pyobjc-framework-Cocoa` are added as macOS-only
  dependencies** so the NSWindow.level bump always works out of the
  box. On other platforms the markers in `pyproject.toml` /
  `requirements.txt` skip them. `start.sh` also tries a best-effort
  install on macOS if the active venv doesn't have them yet.
  新增 macOS 专属依赖 `pyobjc-core` / `pyobjc-framework-Cocoa`（通过
  `sys_platform == 'darwin'` marker 限制），保证 NSWindow.level 调用
  开箱即用。`start.sh` 也会在 macOS venv 没有它们时尽力补装一次。

---

## [0.4.2] – 2026-05-15

### Changed
- **Curated translation language list.** The *Translate From* /
  *Translate To* dropdowns no longer offer dozens of obscure options.
  They are now restricted to the nine languages the project actually
  cares about, in a fixed, intuitive order:
  `简体中文 (zh)`, `繁體中文 (zt)`, `English (en)`, `Français (fr)`,
  `Deutsch (de)`, `日本語 (ja)`, `한국어 (ko)`, `Español (es)`,
  `Русский (ru)`. English-only Whisper models still collapse the
  source dropdown to English alone.
  *Translate From* / *Translate To* 的下拉菜单不再展示几十种冷门语言，
  现在固定在我们关心的 9 种里，按预设顺序排列：简体中文、繁體中文、
  English、Français、Deutsch、日本語、한국어、Español、Русский。
  英文专用的 Whisper 模型仍然会把源语言强制收缩为仅 English。
- Removed the now-unused `WHISPER_LANGUAGE_CODES` and
  `ARGOS_LANGUAGE_CODES` tables from `parrotsub.languages` in favour
  of a single `CURATED_LANGUAGE_CODES` tuple. Existing configs that
  reference a language outside the curated list still keep working —
  the saved value stays selected at the top of the dropdown.
  从 `parrotsub.languages` 移除了不再使用的 `WHISPER_LANGUAGE_CODES`
  和 `ARGOS_LANGUAGE_CODES`，统一为一个 `CURATED_LANGUAGE_CODES`。
  老配置里如果引用了 9 种之外的语言，下拉框会把它保留在最上方继续可用。

---

## [0.4.1] – 2026-05-15

### Fixed
- **App no longer crashes when the saved language code is invalid.**
  The vendored backend used to call `next(filter(...))` on the argos
  package list and raise `StopIteration` when the saved
  `TranslateFrom` / `TranslateTo` codes were wrong (e.g. `"cn"` from
  the pre-v0.4.0 free-text input), bringing the whole app down before
  the UI could even appear. The init now:
  1. Skips the download when the requested language pair is already
     installed locally;
  2. Falls back to "translation disabled, log a warning" when the
     pair is missing from the argos index;
  3. Wraps per-segment translation in a try/except so a single
     failed translation never tears down the worker thread.
  应用因为旧配置里语言代码非法（例如 v0.4.0 之前自由输入的 `"cn"`）
  而崩溃的问题已修复——内嵌后端原本会 `next(filter(...))` 抛
  `StopIteration`，UI 还没来得及出现就已经 crash。现在改为：已安装
  就跳过下载；找不到包就关掉翻译并给出警告；单条翻译失败也不会再
  把后台线程拖垮。

### Added
- `parrotsub.languages.migrate_legacy_code()` and an auto-migration
  pass in `parrotsub.app.launch()` that rewrites well-known invalid
  codes (`cn → zh`, `tw → zt`, `jp → ja`, `kr → ko`, `us/gb → en`)
  in the saved config and persists the fix on first launch.
  新增 `migrate_legacy_code()` 与启动时的自动迁移：把已知的非法/俗
  写代码（`cn → zh`、`tw → zt`、`jp → ja`、`kr → ko`、`us/gb → en`）
  写回成合法的 ISO 代码，下次启动彻底无感。

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

[Unreleased]: https://github.com/21White/ParrotSub/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/21White/ParrotSub/releases/tag/v0.7.0
[0.6.5]: https://github.com/21White/ParrotSub/releases/tag/v0.6.5
[0.6.4]: https://github.com/21White/ParrotSub/releases/tag/v0.6.4
[0.6.3]: https://github.com/21White/ParrotSub/releases/tag/v0.6.3
[0.6.2]: https://github.com/21White/ParrotSub/releases/tag/v0.6.2
[0.6.1]: https://github.com/21White/ParrotSub/releases/tag/v0.6.1
[0.6.0]: https://github.com/21White/ParrotSub/releases/tag/v0.6.0
[0.5.1]: https://github.com/21White/ParrotSub/releases/tag/v0.5.1
[0.5.0]: https://github.com/21White/ParrotSub/releases/tag/v0.5.0
[0.4.2]: https://github.com/21White/ParrotSub/releases/tag/v0.4.2
[0.4.1]: https://github.com/21White/ParrotSub/releases/tag/v0.4.1
[0.4.0]: https://github.com/21White/ParrotSub/releases/tag/v0.4.0
[0.3.0]: https://github.com/21White/ParrotSub/releases/tag/v0.3.0
[0.2.0]: https://github.com/21White/ParrotSub/releases/tag/v0.2.0
