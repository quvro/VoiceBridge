# VoiceBridge 🎤🌉

**AI 同声传译助手** — 实时将外语视频音频翻译成中文字幕。

## 功能

- 🎬 支持网络视频播放，实时采集音频
- 🎤 腾讯云 ASR 流式语音识别（英语）
- 🤖 DeepSeek V4 Flash 智能翻译（英文 → 中文）
- 📝 实时中文字幕展示（支持 interim / final / corrected 状态）
- 🔄 自动上下文纠错，保持术语一致性
- 📋 支持自定义主题和术语表

## 技术栈

| 模块 | 技术 |
|---|---|
| 前端 | React + TypeScript + Vite |
| 音频采集 | Web Audio API (AudioContext → PCM 16kHz) |
| 后端 | Python FastAPI + WebSocket |
| ASR | 腾讯云实时语音识别 |
| 翻译 | DeepSeek V4 Flash |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/quvro/VoiceBridge.git
cd VoiceBridge
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入腾讯云和 DeepSeek 的 API Key
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 5. 打开浏览器

访问 `http://localhost:5173`，输入视频地址，点击"开始翻译"即可体验。

## 项目结构

```
VoiceBridge/
├── frontend/              # React + TypeScript (Vite)
│   ├── src/
│   │   ├── components/    # React 组件
│   │   ├── hooks/         # 自定义 Hooks
│   │   ├── workers/       # AudioWorklet
│   │   └── types/         # TypeScript 类型
│   └── public/            # 静态资源
├── backend/               # Python FastAPI
│   ├── main.py            # WebSocket 服务入口
│   ├── asr_client.py      # 腾讯云 ASR 客户端
│   ├── translator.py      # DeepSeek 翻译
│   ├── context_manager.py # 上下文管理
│   └── config.py          # 配置
└── .env.example           # 环境变量模板
```

## License

MIT
