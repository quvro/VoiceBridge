import { useState, useRef, useCallback } from 'react';
import VideoPlayer, { type VideoPlayerHandle } from './components/VideoPlayer';
import SubtitlePanel from './components/SubtitlePanel';
import ControlBar from './components/ControlBar';
import ConfigPanel from './components/ConfigPanel';
import { useAudioCapture } from './hooks/useAudioCapture';
import { useWebSocket } from './hooks/useWebSocket';
import type { SubtitleSegment, Glossary } from './types';
import './App.css';

const WS_URL = 'ws://localhost:8000/ws';

function App() {
  const [videoSrc, setVideoSrc] = useState('/sample.mp4');
  const [urlInput, setUrlInput] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  const [segments, setSegments] = useState<SubtitleSegment[]>([]);

  const videoPlayerRef = useRef<VideoPlayerHandle>(null);
  const { start: startCapture, stop: stopCapture } = useAudioCapture();
  const { connect, disconnect, sendAudio, sendConfig, sendPause, sendClear, connected } =
    useWebSocket();

  // 字幕处理
  const handleSubtitle = useCallback((seg: SubtitleSegment) => {
    setSegments((prev) => {
      if (seg.id === 'interim') {
        // 替换或添加 interim
        const withoutInterim = prev.filter((s) => s.status !== 'interim');
        return [...withoutInterim, seg];
      }
      const exists = prev.find((s) => s.id === seg.id);
      if (exists) {
        return prev.map((s) => (s.id === seg.id ? seg : s));
      }
      return [...prev, seg];
    });
  }, []);

  const handleCorrection = useCallback((seg: SubtitleSegment) => {
    setSegments((prev) =>
      prev.map((s) => (s.id === seg.id ? seg : s))
    );
  }, []);

  const handleClear = useCallback(() => {
    setSegments([]);
  }, []);

  // 开始翻译
  const handleStart = useCallback(() => {
    const video = videoPlayerRef.current?.getVideoElement();
    if (!video) return;

    // 连接 WebSocket
    connect(WS_URL, handleSubtitle, handleCorrection, handleClear);

    // 开始音频采集
    startCapture(video, (pcmData) => {
      sendAudio(pcmData);
    });

    video.play();
    setIsTranslating(true);
  }, [connect, startCapture, sendAudio, handleSubtitle, handleCorrection, handleClear]);

  // 暂停翻译
  const handlePause = useCallback(() => {
    sendPause();
    stopCapture();
    setIsTranslating(false);
  }, [sendPause, stopCapture]);

  // 清空字幕
  const handleClearSubtitles = useCallback(() => {
    sendClear();
    setSegments([]);
  }, [sendClear]);

  // 加载视频
  const handleLoadVideo = () => {
    if (urlInput.trim()) {
      setVideoSrc(urlInput.trim());
    }
  };

  // 配置变更
  const handleConfigChange = (topic: string, glossary: Glossary) => {
    sendConfig(topic, glossary);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎤 VoiceBridge</h1>
        <span className="subtitle">AI 同声传译助手</span>
      </header>

      <section className="url-bar">
        <input
          type="text"
          placeholder="输入视频 URL（或使用默认示例视频）"
          value={urlInput}
          onChange={(e) => setUrlInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleLoadVideo()}
        />
        <button className="btn" onClick={handleLoadVideo}>加载</button>
      </section>

      <VideoPlayer ref={videoPlayerRef} src={videoSrc} />

      <ControlBar
        isCapturing={isTranslating}
        connected={connected}
        onStart={handleStart}
        onPause={handlePause}
        onClear={handleClearSubtitles}
      />

      <ConfigPanel onConfigChange={handleConfigChange} />

      <SubtitlePanel segments={segments} />
    </div>
  );
}

export default App;
