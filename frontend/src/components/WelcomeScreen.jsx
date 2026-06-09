'use client';

import { useState, useRef, useCallback } from 'react';

const SUGGESTIONS = [
  { label: '광고 시뮬레이션을 해줘' },
  { label: '페르소나를 추가하고 싶어', navigate: 'personas' },
  { label: '광고 이미지를 만들어줘', navigate: 'ad-image' },
];

const FEATURES = [
  { icon: '🎯', label: 'AI 페르소나 반응' },
  { icon: '📊', label: '실시간 성과 분석' },
  { icon: '⚡', label: '다중 에이전트 시뮬레이션' },
];

const NAV_KEYWORDS = ['시뮬', '테스트', '해줘', '하고싶', '하고 싶', '궁금', '분석해', '보여줘', '실행', '시작'];

function extractAdContent(text) {
  const isNavRequest = text.length < 30 || NAV_KEYWORDS.some((k) => text.includes(k));
  return isNavRequest ? '' : text;
}

export default function WelcomeScreen({ onStart, onNavigate }) {
  const [text, setText] = useState('');
  const [leaving, setLeaving] = useState(false);
  const taRef = useRef(null);

  const handleSubmit = useCallback(() => {
    if (!text.trim() || leaving) return;
    setLeaving(true);
    setTimeout(() => onStart(extractAdContent(text.trim())), 350);
  }, [text, leaving, onStart]);

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChipClick = (suggestion) => {
    if (suggestion.navigate) {
      onNavigate?.(suggestion.navigate);
    } else {
      setText(suggestion.label);
      taRef.current?.focus();
    }
  };

  return (
    <div
      className={`min-h-screen bg-brand-bg flex flex-col items-center justify-center p-6 relative overflow-hidden transition-opacity duration-300 ${leaving ? 'opacity-0' : 'opacity-100'}`}
    >
      {/* Ambient blobs */}
      <div
        className="absolute -top-40 -left-28 w-[500px] h-[500px] rounded-full bg-gradient-to-br from-sky-400 to-violet-400 opacity-[0.22] blur-[90px] pointer-events-none animate-blob"
      />
      <div
        className="absolute -bottom-28 -right-20 w-96 h-96 rounded-full bg-gradient-to-br from-emerald-400 to-sky-400 opacity-[0.22] blur-[90px] pointer-events-none animate-blob"
        style={{ animationDelay: '-7s' }}
      />

      <div className="relative z-10 w-full max-w-[680px] flex flex-col items-center">

        {/* Logo / Title */}
        <div className="mb-4 w-14 h-14 rounded-2xl bg-gradient-to-br from-sky-400 to-sky-500 flex items-center justify-center text-2xl shadow-[0_4px_20px_rgba(56,189,248,0.30)]">
          🎯
        </div>
        <h1 className="font-display text-4xl font-black text-brand-text tracking-tight mb-2 text-center">
          Click<span className="text-sky-500">Me</span>
        </h1>
        <p className="text-sm text-brand-muted text-center mb-10 leading-7 font-semibold">
          AI 페르소나가 실제 사람처럼 광고에 반응합니다<br />
          형식적인 AI 평가 없이 — 진짜 반응을 확인하세요
        </p>

        {/* Feature pills */}
        <div className="flex gap-2.5 flex-wrap justify-center mb-9">
          {FEATURES.map((f) => (
            <span
              key={f.label}
              className="flex items-center gap-1.5 px-4 py-2 bg-white border border-sky-400/20 rounded-full text-xs font-bold text-brand-muted shadow-sm"
            >
              {f.icon} {f.label}
            </span>
          ))}
        </div>

        {/* Input box */}
        <div className="w-full px-10">
          <div className="bg-white border-[1.5px] border-sky-400/20 rounded-2xl p-3.5 flex items-end gap-2.5 shadow-[0_8px_32px_rgba(56,189,248,0.12)] focus-within:border-sky-400 focus-within:shadow-[0_8px_32px_rgba(56,189,248,0.28)] transition-all">
            <textarea
              ref={taRef}
              className="flex-1 bg-transparent text-sm text-brand-text placeholder-brand-light outline-none resize-none leading-relaxed max-h-[120px] overflow-y-auto"
              rows={2}
              placeholder="무엇을 테스트하고 싶으신가요? (예: 광고 시뮬레이션을 해줘)"
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKey}
            />
            <button
              onClick={handleSubmit}
              disabled={!text.trim() || leaving}
              className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 to-sky-500 disabled:from-brand-bg2 disabled:to-brand-bg2 disabled:text-brand-light text-white text-xl flex items-center justify-center shrink-0 transition-all hover:scale-110 hover:rotate-[8deg] active:scale-95 shadow-[0_4px_14px_rgba(56,189,248,0.28)]"
              aria-label="시작"
            >
              ↑
            </button>
          </div>
        </div>

        {/* Quick chips */}
        <div className="flex flex-wrap gap-2 mt-3.5 justify-center px-10">
          {SUGGESTIONS.map((s) => (
            <button
              key={s.label}
              onClick={() => handleChipClick(s)}
              className={`px-3.5 py-1.5 text-xs font-bold rounded-full transition-all hover:-translate-y-0.5 ${
                s.navigate
                  ? 'text-sky-600 bg-sky-100 border border-sky-400/40 hover:bg-sky-200 hover:border-sky-400/60'
                  : 'text-brand-muted bg-sky-50 border border-sky-400/20 hover:bg-sky-100 hover:text-sky-600 hover:border-sky-400/40'
              }`}
            >
              {s.navigate === 'personas' ? '👤 ' : s.navigate === 'ad-image' ? '🎨 ' : ''}{s.label}
            </button>
          ))}
        </div>

      </div>
    </div>
  );
}
