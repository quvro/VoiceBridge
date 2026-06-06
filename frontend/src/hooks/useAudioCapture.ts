/** 音频采集 Hook */
import { useRef, useCallback } from 'react';

export function useAudioCapture() {
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const capturingRef = useRef(false);
  const workletLoadedRef = useRef(false);

  const onPcmDataRef = useRef<((data: ArrayBuffer) => void) | null>(null);

  const start = useCallback(async (
    videoElement: HTMLVideoElement,
    onPcmData: (data: ArrayBuffer) => void
  ) => {
    if (capturingRef.current) return;

    onPcmDataRef.current = onPcmData;

    try {
      let ctx = audioContextRef.current;
      const videoChanged = videoRef.current !== videoElement;

      // ---- 创建/恢复 AudioContext ----
      if (!ctx || ctx.state === 'closed') {
        ctx = new AudioContext();
        audioContextRef.current = ctx;
        workletLoadedRef.current = false;
      }

      if (ctx.state === 'suspended') {
        await ctx.resume();
      }

      // ---- 视频变了或首次 —— 需要重建 source ----
      if (videoChanged || !sourceRef.current) {
        // 清理旧 source
        if (sourceRef.current) {
          try { sourceRef.current.disconnect(); } catch {}
          sourceRef.current = null;
        }
        if (workletNodeRef.current) {
          try { workletNodeRef.current.disconnect(); } catch {}
          workletNodeRef.current = null;
        }

        // 加载 AudioWorklet（只加载一次）
        if (!workletLoadedRef.current) {
          await ctx.audioWorklet.addModule('/src/workers/audio-processor.js');
          workletLoadedRef.current = true;
        }

        // createMediaElementSource 对同一 video 只能调用一次
        const source = ctx.createMediaElementSource(videoElement);
        sourceRef.current = source;
        videoRef.current = videoElement;

        const workletNode = new AudioWorkletNode(ctx, 'audio-processor');
        workletNodeRef.current = workletNode;

        workletNode.port.onmessage = (event: MessageEvent<ArrayBuffer>) => {
          onPcmDataRef.current?.(event.data);
        };

        source.connect(workletNode);
        workletNode.connect(ctx.destination);
      }

      capturingRef.current = true;
    } catch (e) {
      // 初始化失败 → 重置状态，允许重试
      capturingRef.current = false;
      console.error('Audio capture failed:', e);
    }
  }, []);

  const stop = useCallback(() => {
    // suspend（不 close），保留 source 供下次 play 复用
    audioContextRef.current?.suspend().catch(() => {});
    capturingRef.current = false;
  }, []);

  return { start, stop };
}
