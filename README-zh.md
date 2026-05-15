# 🦜 ParrotSub（中文）

> 面向 Apple Silicon Mac 的离线实时语音转字幕桌面应用，自带一套清爽的
> shadcn 风格 UI。

ParrotSub 把麦克风听到的声音实时变成原文字幕和（可选的）翻译，全程
本地运行。仓库内含两块代码：

1. **`parrotsub`**：现代化的 PyQt6 桌面 UI——侧边栏 + Header 应用框架、
   明暗双主题、贴近鹦鹉调性的 teal 主色、可拖动的置顶悬浮字幕窗、
   导出会话浏览器。
2. **`realtime_subtitle`**：底层离线管线，从
   [@caoqiming](https://github.com/caoqiming/realtime-subtitle) 的 MIT
   项目内嵌而来，负责麦克风采集（PyAudio）、语音识别（`mlx-whisper`）、
   翻译（`argos-translate` 或在线）、声纹聚类（`speechbrain`），并把
   结果导出为 `audio.wav`、`subtitles.srt`、`subtitles.lrc` 以及一个
   可交互的 `transcription.html`。

GitHub：<https://github.com/21White/ParrotSub>

## 主要特性

- **侧边栏 + Header 应用框架**：56px 图标导航条（Tasks / Settings /
  Exports）、57px 顶部栏（标题 / 版本号 / 实时状态胶囊）。
- **shadcn 风格主题**：统一设计 token、明暗双套调色板、属于鹦鹉品牌的
  teal 主色（亮 `#0d9488` / 暗 `#14b8a6`），所有主操作和激活态都用它。
- **Tasks 页**：开始 / 停止录音、原文与译文双卡片实时刷新、两个置顶
  悬浮窗的独立开关、一键导出。
- **Settings 页**：把后端的所有配置字段拆成 6 张卡片（音频输入 /
  Whisper 模型 / 翻译 / 字幕排版 / 悬浮窗 / 声纹与存储），按字段类型
  自动生成下拉框、开关或文本框，提供保存与重置。
- **悬浮字幕窗**：无边框、半透明、可鼠标拖动、置顶，文字带描边便于
  在任意背景上阅读。
- **Exports 页**：列出每一次导出会话，标注它包含哪些产物
  （`audio.wav` / `subtitles.srt` / `subtitles.lrc` /
  `transcription.html`），双击直接在 Finder 中打开。
- **完全自包含**：不依赖任何外部 PyPI 上的同名包，UI 与后端都在这一
  个仓库内一起发布。

## 环境要求

- Apple Silicon Mac（mlx-whisper 限制）
- Python ≥ 3.9
- `portaudio`（`brew install portaudio`）

## 安装

```bash
git clone https://github.com/21White/ParrotSub.git
cd ParrotSub

brew install portaudio

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

> **提示**：上游后端把 `speechbrain` 钉死在 1.0.3，但它在
> `torchaudio>=2.9` 上会报错。ParrotSub 的依赖里直接覆盖成
> `speechbrain>=1.1.0`，开箱即用。

## 启动

```bash
parrotsub
# 等价于
parrotsub ui
# 或
python -m parrotsub
```

也可以直接 `./start.sh`：会自动激活 `./.venv`、设 `HF_ENDPOINT` 国内
镜像，并在需要时把 ParrotSub 安装到当前环境，然后启动 UI。

直接离线解析单个 WAV 文件：

```bash
parrotsub parse -f my-audio.wav
# 也可以用旧入口名
realtime-subtitle parse -f my-audio.wav
```

## 仓库结构

```
ParrotSub/
├── README.md                # 英文 README
├── README-zh.md             # 本文档
├── LICENSE                  # Apache-2.0（ParrotSub 自己）
├── NOTICE                   # 第三方组件归属说明
├── THIRD_PARTY_LICENSES/
│   └── realtime-subtitle.LICENSE   # MIT，内嵌后端的版权声明
├── pyproject.toml
├── requirements.txt
├── environment.yml
├── start.sh
├── .gitignore
└── src/
    ├── parrotsub/           # UI 壳
    │   ├── __init__.py / __main__.py / cli.py
    │   ├── theme.py / icons.py / app.py
    │   ├── widgets/         # card / sidebar / header / status_pill /
    │   │                    # switch / subtitle_view / floating / icon_button
    │   └── pages/           # home / settings / exports
    └── realtime_subtitle/    # 内嵌的离线后端（MIT，glimmer）
        ├── app_config.py / common.py / cli.py
        ├── parse_audio.py / subtitle.py
        ├── glimmer_speech_recognition.py
        ├── template.html
        └── ui.py            # 上游原始 PyQt6 UI（保留以保持兼容）
```

## 配置

配置文件保持与上游兼容，仍然写在
`~/.config/glimmer/realtime-subtitle.config`，所以从老项目迁过来的
配置可以原地继续使用。修改方式有两种：在 UI 的 **Settings** 页面修改
后保存；或者直接编辑那个 JSON 文件。

导出默认写到 `~/Desktop/realtime-subtitle/<时间戳>/`，可以从 **Exports**
页面浏览。

## 致谢

- 离线语音识别管线：从
  [`realtime-subtitle`](https://github.com/caoqiming/realtime-subtitle)
  内嵌而来，原作者 [@caoqiming](https://github.com/caoqiming)，MIT
  许可证；版权声明保留在 `THIRD_PARTY_LICENSES/`。
- Whisper 推理：[`mlx-whisper`](https://github.com/ml-explore/mlx-examples)
- 离线翻译：[`argos-translate`](https://github.com/argosopentech/argos-translate)
- 声纹识别：[`speechbrain`](https://github.com/speechbrain/speechbrain)
- 图标：[`lucide`](https://lucide.dev)（在 Qt 里重新渲染）
- 设计 token：[`shadcn/ui`](https://ui.shadcn.com) 的 HSL 色板，
  在 QSS 中以等价的 hex 表达

## 许可证

ParrotSub 采用 **Apache License 2.0**，详见 [`LICENSE`](./LICENSE) 与
[`NOTICE`](./NOTICE)。

`src/realtime_subtitle/` 内嵌的离线后端继续沿用原作者的 **MIT 许可证**
（Copyright (c) 2025 glimmer），其完整许可文本按要求保留在
[`THIRD_PARTY_LICENSES/realtime-subtitle.LICENSE`](./THIRD_PARTY_LICENSES/realtime-subtitle.LICENSE)。
