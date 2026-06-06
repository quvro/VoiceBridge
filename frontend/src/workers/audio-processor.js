/**
 * AudioWorklet Processor - 降采样 48kHz→16kHz 并输出 Int16 PCM
 * 运行在 AudioWorklet 独立线程中
 */
class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = new Float32Array(3200); // 200ms @ 16kHz
    this.bufferOffset = 0;
    this.targetSampleRate = 16000;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;

    const channel = input[0];
    if (!channel) return true;

    const inputSampleRate = globalThis.sampleRate; // 通常 44100 或 48000
    const ratio = inputSampleRate / this.targetSampleRate;

    // 简单降采样：每隔 ratio 个 sample 取 1 个
    for (let i = 0; i < channel.length; i++) {
      const srcIndex = Math.floor(this.bufferOffset * ratio);
      if (srcIndex < channel.length) {
        this.buffer[this.bufferOffset] = channel[srcIndex];
        this.bufferOffset++;

        if (this.bufferOffset >= this.buffer.length) {
          // Float32 → Int16 PCM
          const int16 = new Int16Array(this.buffer.length);
          for (let j = 0; j < this.buffer.length; j++) {
            const sample = Math.max(-1, Math.min(1, this.buffer[j]));
            int16[j] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
          }
          this.port.postMessage(int16.buffer, [int16.buffer]);
          this.bufferOffset = 0;
          this.buffer = new Float32Array(3200);
        }
      }
    }

    return true;
  }
}

registerProcessor('audio-processor', AudioProcessor);
