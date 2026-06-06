/**
 * AudioWorklet Processor - 降采样到 16kHz 并输出 Int16 PCM
 * 运行在 AudioWorklet 独立线程中
 *
 * 输入: 浏览器默认采样率（通常 44.1kHz/48kHz）Float32
 * 输出: 每 200ms 一个 Int16 PCM 16kHz chunk (3200 samples = 6400 bytes)
 */
class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    // 输入缓冲: 能容纳 200ms @ 48kHz = 9600 samples
    this.inputBuffer = new Float32Array(19200);
    this.inputOffset = 0;
    this.targetRate = 16000;
    this.chunkSamples = 3200; // 200ms @ 16kHz
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;

    const channel = input[0];
    if (!channel) return true;

    const inputRate = globalThis.sampleRate; // 浏览器实际采样率
    const ratio = inputRate / this.targetRate;

    // 累积输入样本到 buffer
    for (let i = 0; i < channel.length; i++) {
      if (this.inputOffset < this.inputBuffer.length) {
        this.inputBuffer[this.inputOffset++] = channel[i];
      }
    }

    // 需要多少输入样本才能产出一个 chunk
    const neededInput = Math.ceil(this.chunkSamples * ratio);

    // 产出 PCM chunk（可能产出多个）
    while (this.inputOffset >= neededInput) {
      const int16 = new Int16Array(this.chunkSamples);
      for (let j = 0; j < this.chunkSamples; j++) {
        const srcIdx = Math.floor(j * ratio);
        const sample = Math.max(-1, Math.min(1, this.inputBuffer[srcIdx]));
        int16[j] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
      }
      // 发送 PCM 给主线程
      this.port.postMessage(int16.buffer, [int16.buffer]);

      // 移除已用样本，shift remaining to front
      const remaining = this.inputOffset - neededInput;
      for (let k = 0; k < remaining; k++) {
        this.inputBuffer[k] = this.inputBuffer[neededInput + k];
      }
      this.inputOffset = remaining;
    }

    return true;
  }
}

registerProcessor('audio-processor', AudioProcessor);
