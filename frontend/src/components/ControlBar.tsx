interface Props {
  connected: boolean;
  onClear: () => void;
}

export default function ControlBar({ connected, onClear }: Props) {
  return (
    <div className="control-bar">
      <button className="btn btn-secondary" onClick={onClear}>
        🗑 清空字幕
      </button>
      <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
        {connected ? '🟢 实时翻译中' : '🔴 未连接'}
      </span>
    </div>
  );
}
