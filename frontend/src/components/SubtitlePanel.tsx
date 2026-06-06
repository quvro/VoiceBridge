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

  // 获取当前显示的最后一条（interim 或最新 final）
  const lastSegment = segments.length > 0 ? segments[segments.length - 1] : null;

  return (
    <div className="subtitle-panel">
      {!lastSegment && (
        <div className="subtitle-placeholder">
          等待字幕...
        </div>
      )}
      {lastSegment && (
        <div className={`subtitle-item ${statusClass(lastSegment.status)}`}>
          {lastSegment.sourceText && (
            <div className="subtitle-source">{lastSegment.sourceText}</div>
          )}
          <div className="subtitle-translated">
            {lastSegment.translatedText || '...'}
          </div>
          {lastSegment.status === 'interim' && <span className="subtitle-badge">识别中</span>}
          {lastSegment.status === 'corrected' && <span className="subtitle-badge corrected">已修正</span>}
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
