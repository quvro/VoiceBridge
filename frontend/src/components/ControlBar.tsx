interface Props {
  isCapturing: boolean;
  connected: boolean;
  onStart: () => void;
  onPause: () => void;
  onClear: () => void;
}

export default function ControlBar({ isCapturing, connected, onStart, onPause, onClear }: Props) {
  return (
    <div className="control-bar">
      {!isCapturing ? (
        <button className="btn btn-primary" onClick={onStart} disabled={!connected}>
          ▶ 开始翻译
        </button>
      ) : (
        <button className="btn btn-warning" onClick={onPause}>
          ⏸ 暂停
        </button>
      )}
      <button className="btn btn-secondary" onClick={onClear}>
        🗑 清空
      </button>
      <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
        {connected ? '🟢 已连接' : '🔴 未连接'}
      </span>
    </div>
  );
}
