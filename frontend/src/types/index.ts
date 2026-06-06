/** VoiceBridge 类型定义 */

export interface SubtitleSegment {
  id: string;
  startTime: number;
  endTime: number;
  sourceText: string;
  translatedText: string;
  status: 'interim' | 'final' | 'corrected';
  version: number;
}

export interface WSMessage {
  type: 'subtitle' | 'correction' | 'clear';
  segment?: SubtitleSegment;
}

export interface Glossary {
  [key: string]: string;
}
