import { useEffect, useRef } from 'react';
import type { SubtitleSegment } from '../types';

interface Props {
  segments: SubtitleSegment[];
}

function statusClass(status: string): string {
  switch (status) {
    case 'interim': return 'subtitle-interim';
    case 'corrected': return 'subtitle-corrected';
    default: return 'subtitle-final';
  }
}

export default function SubtitlePanel({ segments }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [segments]);

  return (
    <div className="subtitle-panel">
      {segments.length === 0 && (
        <div className="subtitle-placeholder">
          等待字幕...
        </div>
      )}
      {segments.map((seg) => (
        <div key={seg.id} className={`subtitle-item ${statusClass(seg.status)}`}>
          <span className="subtitle-text">{seg.translatedText || seg.sourceText}</span>
          {seg.status === 'interim' && <span className="subtitle-badge">识别中</span>}
          {seg.status === 'corrected' && <span className="subtitle-badge corrected">已修正</span>}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
