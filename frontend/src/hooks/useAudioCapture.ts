/** 音频采集 Hook */
import { useRef, useCallback, useState } from 'react';

export function useAudioCapture() {
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);

  const onPcmDataRef = useRef<((data: ArrayBuffer) => void) | null>(null);

  const start = useCallback(async (
    videoElement: HTMLVideoElement,
    onPcmData: (data: ArrayBuffer) => void
  ) => {
    if (isCapturing) return;

    onPcmDataRef.current = onPcmData;

    const ctx = new AudioContext({ sampleRate: 48000 });
    audioContextRef.current = ctx;

    // 加载 AudioWorklet
    await ctx.audioWorklet.addModule('/src/workers/audio-processor.js');

    // 连接到 video 元素
    const source = ctx.createMediaElementSource(videoElement);
    sourceRef.current = source;

    const workletNode = new AudioWorkletNode(ctx, 'audio-processor');
    workletNodeRef.current = workletNode;

    // 接收 AudioWorklet 输出的 Int16 PCM
    workletNode.port.onmessage = (event: MessageEvent<ArrayBuffer>) => {
      onPcmDataRef.current?.(event.data);
    };

    source.connect(workletNode);
    workletNode.connect(ctx.destination);

    setIsCapturing(true);
  }, [isCapturing]);

  const stop = useCallback(() => {
    sourceRef.current?.disconnect();
    workletNodeRef.current?.disconnect();
    audioContextRef.current?.close();
    sourceRef.current = null;
    workletNodeRef.current = null;
    audioContextRef.current = null;
    setIsCapturing(false);
  }, []);

  return { start, stop, isCapturing };
}
