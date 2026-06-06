/** WebSocket 通信 Hook */
import { useRef, useCallback, useState } from 'react';
import type { SubtitleSegment, Glossary } from '../types';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const onSubtitleRef = useRef<((seg: SubtitleSegment) => void) | null>(null);
  const onCorrectionRef = useRef<((seg: SubtitleSegment) => void) | null>(null);
  const onClearRef = useRef<(() => void) | null>(null);

  const connect = useCallback((
    url: string,
    onSubtitle: (seg: SubtitleSegment) => void,
    onCorrection: (seg: SubtitleSegment) => void,
    onClear: () => void,
  ) => {
    onSubtitleRef.current = onSubtitle;
    onCorrectionRef.current = onCorrection;
    onClearRef.current = onClear;

    const ws = new WebSocket(url);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'subtitle' && msg.segment) {
          onSubtitleRef.current?.(msg.segment);
        } else if (msg.type === 'correction' && msg.segment) {
          onCorrectionRef.current?.(msg.segment);
        } else if (msg.type === 'clear') {
          onClearRef.current?.();
        }
      } catch {
        // 忽略解析错误
      }
    };

    wsRef.current = ws;
  }, []);

  const sendAudio = useCallback((data: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  const sendConfig = useCallback((topic: string, glossary: Glossary) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'config', topic, glossary }));
    }
  }, []);

  const sendPause = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ type: 'pause' }));
  }, []);

  const sendResume = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ type: 'resume' }));
  }, []);

  const sendClear = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ type: 'clear' }));
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  return { connect, disconnect, sendAudio, sendConfig, sendPause, sendResume, sendClear, connected };
}
