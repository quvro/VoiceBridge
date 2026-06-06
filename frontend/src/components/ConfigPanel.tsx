import { useState } from 'react';
import type { Glossary } from '../types';

interface Props {
  onConfigChange: (topic: string, glossary: Glossary) => void;
}

export default function ConfigPanel({ onConfigChange }: Props) {
  const [topic, setTopic] = useState('');
  const [glossaryText, setGlossaryText] = useState('');

  const parseGlossary = (text: string): Glossary => {
    const glossary: Glossary = {};
    text.split('\n').forEach((line) => {
      const parts = line.split('=');
      if (parts.length === 2) {
        glossary[parts[0].trim()] = parts[1].trim();
      }
    });
    return glossary;
  };

  const handleApply = () => {
    onConfigChange(topic, parseGlossary(glossaryText));
  };

  return (
    <div className="config-panel">
      <div className="config-row">
        <label>主题：</label>
        <input
          type="text"
          placeholder="如：AI 技术分享、经济学讲座..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        />
      </div>
      <div className="config-row">
        <label>术语表：</label>
        <textarea
          rows={3}
          placeholder={`cache=缓存\npipeline=流水线\nmodel=模型`}
          value={glossaryText}
          onChange={(e) => setGlossaryText(e.target.value)}
        />
      </div>
      <button className="btn btn-small" onClick={handleApply}>
        应用配置
      </button>
    </div>
  );
}
