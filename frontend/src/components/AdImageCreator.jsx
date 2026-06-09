'use client';

import { useState, useRef, useCallback } from 'react';

const STYLE_OPTIONS = [
  { id: 'modern', label: '모던 & 미니멀', icon: '✨' },
  { id: 'bold', label: '강렬 & 임팩트', icon: '⚡' },
  { id: 'warm', label: '따뜻 & 감성적', icon: '🌿' },
  { id: 'luxury', label: '럭셔리 & 프리미엄', icon: '💎' },
];

export default function AdImageCreator({ onBack }) {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [selectedStyle, setSelectedStyle] = useState('modern');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith('image/')) return;
    setUploadedImage(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);
      handleFile(e.dataTransfer.files[0]);
    },
    [handleFile]
  );

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleInputChange = (e) => handleFile(e.target.files[0]);

  const handleRemove = () => {
    setUploadedImage(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col relative overflow-hidden">
      {/* Ambient blobs */}
      <div className="absolute -top-40 -left-28 w-[500px] h-[500px] rounded-full bg-gradient-to-br from-sky-400 to-violet-400 opacity-[0.18] blur-[90px] pointer-events-none" />
      <div className="absolute -bottom-28 -right-20 w-96 h-96 rounded-full bg-gradient-to-br from-emerald-400 to-sky-400 opacity-[0.18] blur-[90px] pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 flex items-center gap-3 px-6 py-4 border-b border-sky-400/10">
        <button
          onClick={onBack}
          className="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-sky-50 text-brand-muted hover:text-sky-500 transition-all text-lg"
          aria-label="뒤로가기"
        >
          ←
        </button>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-400 to-sky-400 flex items-center justify-center text-base shadow-[0_2px_10px_rgba(139,92,246,0.25)]">
            🎨
          </div>
          <div>
            <h1 className="text-sm font-black text-brand-text tracking-tight leading-none">
              광고 이미지 제작
            </h1>
            <p className="text-[11px] text-brand-muted mt-0.5">AI로 광고 이미지를 최적화하세요</p>
          </div>
        </div>
        <span className="ml-auto px-2.5 py-1 text-[10px] font-bold rounded-full bg-violet-100 text-violet-500 border border-violet-300/40">
          Coming Soon
        </span>
      </header>

      {/* Body */}
      <main className="relative z-10 flex-1 flex flex-col lg:flex-row gap-6 p-6 max-w-5xl mx-auto w-full">

        {/* Left panel — upload + options */}
        <section className="flex-1 flex flex-col gap-5">

          {/* Upload zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => !previewUrl && fileInputRef.current?.click()}
            className={`relative rounded-2xl border-2 border-dashed transition-all overflow-hidden
              ${previewUrl
                ? 'border-sky-400/30 cursor-default'
                : `border-sky-400/30 hover:border-sky-400/60 hover:bg-sky-50/50 cursor-pointer ${isDragging ? 'border-sky-400 bg-sky-50/80 scale-[1.01]' : ''}`
              }
            `}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleInputChange}
            />

            {previewUrl ? (
              <div className="relative">
                <img
                  src={previewUrl}
                  alt="업로드된 광고 이미지"
                  className="w-full max-h-72 object-contain bg-brand-bg2"
                />
                <button
                  onClick={handleRemove}
                  className="absolute top-3 right-3 w-8 h-8 rounded-full bg-white/90 border border-sky-400/20 text-brand-muted hover:text-red-400 hover:border-red-300/40 text-sm font-bold transition-all flex items-center justify-center shadow-sm"
                  aria-label="이미지 삭제"
                >
                  ✕
                </button>
                <div className="px-4 py-2.5 flex items-center gap-2 border-t border-sky-400/10">
                  <span className="text-xs text-brand-muted truncate">{uploadedImage?.name}</span>
                  <button
                    onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                    className="ml-auto text-xs font-bold text-sky-500 hover:text-sky-600 shrink-0"
                  >
                    변경
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-14 px-6 text-center">
                <div className="w-14 h-14 rounded-2xl bg-sky-50 border border-sky-400/20 flex items-center justify-center text-2xl mb-4">
                  🖼️
                </div>
                <p className="text-sm font-bold text-brand-text mb-1">
                  광고 이미지를 업로드하세요
                </p>
                <p className="text-xs text-brand-muted mb-4">
                  드래그 & 드롭 또는 클릭하여 선택
                </p>
                <span className="px-4 py-2 text-xs font-bold text-sky-600 bg-sky-50 border border-sky-400/30 rounded-full hover:bg-sky-100 transition-colors">
                  파일 선택
                </span>
                <p className="text-[10px] text-brand-light mt-4">JPG, PNG, WEBP · 최대 10MB</p>
              </div>
            )}
          </div>

          {/* Style selector */}
          <div className="bg-white rounded-2xl border border-sky-400/15 p-4 shadow-sm">
            <p className="text-xs font-black text-brand-text mb-3 uppercase tracking-wider">스타일 선택</p>
            <div className="grid grid-cols-2 gap-2">
              {STYLE_OPTIONS.map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => setSelectedStyle(opt.id)}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-xl border text-xs font-bold transition-all
                    ${selectedStyle === opt.id
                      ? 'bg-sky-50 border-sky-400/50 text-sky-600'
                      : 'bg-brand-bg2 border-sky-400/10 text-brand-muted hover:border-sky-400/30 hover:text-sky-500'
                    }`}
                >
                  <span>{opt.icon}</span>
                  <span>{opt.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Modify button */}
          <button
            disabled
            className="w-full py-3.5 rounded-2xl bg-gradient-to-br from-violet-400 to-sky-400 text-white font-black text-sm opacity-40 cursor-not-allowed flex items-center justify-center gap-2 shadow-[0_4px_18px_rgba(139,92,246,0.20)]"
          >
            🎨 이미지 최적화하기
          </button>
        </section>

        {/* Right panel — result */}
        <section className="flex-1 flex flex-col gap-5">
          <div className="bg-white rounded-2xl border border-sky-400/15 shadow-sm flex-1 flex flex-col overflow-hidden">
            <div className="px-4 py-3.5 border-b border-sky-400/10 flex items-center gap-2">
              <span className="text-sm font-black text-brand-text">수정된 이미지</span>
              <span className="ml-auto text-[10px] font-bold text-violet-400 bg-violet-50 border border-violet-200/50 rounded-full px-2 py-0.5">
                Preview
              </span>
            </div>

            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center min-h-64">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-100 to-sky-100 border border-violet-200/40 flex items-center justify-center text-2xl mb-5">
                🚀
              </div>
              <p className="text-sm font-black text-brand-text mb-2">곧 출시됩니다</p>
              <p className="text-xs text-brand-muted leading-relaxed max-w-52">
                AI가 광고 이미지를 분석하고<br />
                성과를 높이는 방향으로 자동 최적화합니다
              </p>

              <div className="mt-8 w-full max-w-64 space-y-2.5">
                {[
                  { icon: '🎯', text: '타겟 페르소나 맞춤 스타일 적용' },
                  { icon: '📐', text: '레이아웃 & 가독성 개선' },
                  { icon: '🎨', text: '색상 & 대비 최적화' },
                  { icon: '✍️', text: '카피 문구 자동 개선 제안' },
                ].map((item) => (
                  <div
                    key={item.text}
                    className="flex items-center gap-2.5 px-3.5 py-2.5 bg-brand-bg2 rounded-xl border border-sky-400/10"
                  >
                    <span className="text-sm">{item.icon}</span>
                    <span className="text-xs text-brand-muted font-semibold">{item.text}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Comparison placeholder */}
          <div className="bg-white rounded-2xl border border-sky-400/15 shadow-sm p-4">
            <p className="text-xs font-black text-brand-text mb-3 uppercase tracking-wider">성과 예측</p>
            <div className="space-y-2.5">
              {[
                { label: '클릭률 (CTR)', before: '—', after: '—' },
                { label: '전환율 (CVR)', before: '—', after: '—' },
                { label: '페르소나 호감도', before: '—', after: '—' },
              ].map((row) => (
                <div key={row.label} className="flex items-center gap-3 text-xs">
                  <span className="text-brand-muted w-28 shrink-0 font-semibold">{row.label}</span>
                  <span className="px-2 py-1 rounded-lg bg-brand-bg2 text-brand-light font-bold w-12 text-center">
                    {row.before}
                  </span>
                  <span className="text-brand-light">→</span>
                  <span className="px-2 py-1 rounded-lg bg-sky-50 text-sky-300 font-bold w-12 text-center">
                    {row.after}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
