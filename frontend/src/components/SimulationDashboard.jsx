'use client';

import { useState, useRef, useCallback, useMemo, useEffect } from "react";
import { useSimulation } from "../hooks/useSimulation";
import MetricsPanel from "./MetricsPanel";
import CognitiveTimeline from "./CognitiveTimeline";
import PersonaFeedbackCard from "./PersonaFeedbackCard";

const AD_TYPE_OPTIONS = ["IMAGE", "VIDEO"];
const AD_TYPE_LABELS = { IMAGE: "이미지", VIDEO: "영상" };

const ACCEPTED_IMAGE = ["image/jpeg", "image/png", "image/gif", "image/webp"];
const ACCEPTED_VIDEO = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"];
const ACCEPTED_ALL = [...ACCEPTED_IMAGE, ...ACCEPTED_VIDEO];

function formatFileSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

function formatTime(ts) {
  const diff = Date.now() - ts;
  if (diff < 60000) return "방금 전";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`;
  return new Date(ts).toLocaleDateString("ko-KR", { month: "short", day: "numeric" });
}

const VERDICT_SHORT = {
  "집행 권장":     { label: "권장", color: "bg-emerald-500" },
  "수정 후 재검토": { label: "재검토", color: "bg-amber-500" },
  "집행 비권장":   { label: "비권장", color: "bg-red-500" },
};

export default function SimulationDashboard({ initialContent = "", onBack, personas = [], activePersonaIds = new Set(), onManagePersonas }) {
  const { result, loading, error, simulate, reset } = useSimulation();

  const [adContent, setAdContent] = useState(initialContent);
  const [adType, setAdType] = useState("IMAGE");
  const [mediaFile, setMediaFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [fileError, setFileError] = useState(null);
  const fileInputRef = useRef(null);

  const [history, setHistory] = useState([]);
  const [selectedId, setSelectedId] = useState(null);


  const handleFile = useCallback((file) => {
    if (!file) return;
    setFileError(null);
    if (!ACCEPTED_ALL.includes(file.type)) {
      setFileError("JPG·PNG·GIF·WEBP 이미지 또는 MP4·MOV·AVI·WEBM 영상만 업로드 가능합니다.");
      return;
    }
    const isVideo = ACCEPTED_VIDEO.includes(file.type);
    const maxBytes = isVideo ? 50 * 1024 * 1024 : 10 * 1024 * 1024;
    if (file.size > maxBytes) {
      setFileError(isVideo ? "영상은 50MB 이하만 가능합니다." : "이미지는 10MB 이하만 가능합니다.");
      return;
    }
    setMediaFile(file);
    setAdType(isVideo ? "VIDEO" : "IMAGE");
    setPreviewUrl(URL.createObjectURL(file));
  }, []);

  const handleFileInput = useCallback((e) => {
    handleFile(e.target.files?.[0]);
    e.target.value = "";
  }, [handleFile]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files?.[0]);
  }, [handleFile]);

  useEffect(() => {
    return () => { if (previewUrl) URL.revokeObjectURL(previewUrl); };
  }, [previewUrl]);

  const removeMedia = useCallback(() => {
    setMediaFile(null);
    setPreviewUrl(null);
    setFileError(null);
  }, []);

  const isVideo = useMemo(
    () => mediaFile != null && ACCEPTED_VIDEO.includes(mediaFile.type),
    [mediaFile],
  );

  const activeCount = useMemo(
    () => personas.filter((p) => activePersonaIds.has(p.persona_id)).length,
    [personas, activePersonaIds],
  );

  const canSubmit = useMemo(
    () => !loading && activeCount > 0 && (adContent.trim().length >= 10 || mediaFile != null),
    [loading, activeCount, adContent, mediaFile],
  );

  const handleReset = useCallback(() => {
    reset();
    removeMedia();
    setAdContent("");
    setSelectedId(null);
  }, [reset, removeMedia]);

  const pendingMetaRef = useRef(null);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    if (!canSubmit) return;
    const id = `ad-${Date.now()}`;
    pendingMetaRef.current = {
      id, adContent, adType,
      mediaFileName: mediaFile?.name ?? null, timestamp: Date.now(),
    };
    simulate({
      adId: id,
      adContent,
      adType,
      personaIds: personas.filter((p) => activePersonaIds.has(p.persona_id)).map((p) => p.persona_id),
      customPersonas: [],
      mediaFile: mediaFile ?? undefined,
    });
  }, [canSubmit, simulate, adContent, adType, mediaFile, personas, activePersonaIds]);

  useEffect(() => {
    if (!result || !pendingMetaRef.current) return;
    const meta = pendingMetaRef.current;
    pendingMetaRef.current = null;
    const entry = { ...meta, result };
    setHistory(prev => [entry, ...prev]);
    setSelectedId(entry.id);
  }, [result]);

  const displayedResult = useMemo(() => {
    if (!selectedId) return result;
    return history.find(h => h.id === selectedId)?.result ?? result;
  }, [selectedId, history, result]);

  return (
    <div className="h-screen bg-brand-bg text-brand-text flex overflow-hidden">
      {/* ── 왼쪽 히스토리 사이드바 ── */}
      <aside className="w-60 shrink-0 border-r border-sky-400/15 bg-white flex flex-col h-full">
        <div className="px-4 py-4 border-b border-sky-400/15">
          <p className="text-[10px] font-black uppercase tracking-widest text-brand-muted">테스트 기록</p>
        </div>
        <div className="flex-1 overflow-y-auto">
          {history.length === 0 ? (
            <div className="px-4 py-8 text-center">
              <p className="text-xs text-brand-light">아직 테스트 기록이 없습니다.</p>
              <p className="text-xs text-brand-light mt-1">시뮬레이션을 실행하면 여기에 표시됩니다.</p>
            </div>
          ) : (
            <ul className="py-2">
              {history.map((h) => {
                const verdict = h.result?.conclusion?.verdict;
                const vs = verdict ? VERDICT_SHORT[verdict] : null;
                const isActive = h.id === selectedId;
                const label = h.adContent?.trim()
                  ? h.adContent.trim().slice(0, 40) + (h.adContent.trim().length > 40 ? "…" : "")
                  : h.mediaFileName
                    ? `📎 ${h.mediaFileName}`
                    : "광고 텍스트";
                return (
                  <li key={h.id}>
                    <button
                      onClick={() => setSelectedId(h.id)}
                      className={`w-full text-left px-4 py-3 transition-colors border-l-2 ${
                        isActive
                          ? "border-sky-400 bg-sky-50"
                          : "border-transparent hover:bg-brand-bg"
                      }`}
                    >
                      <p className="text-xs text-brand-text font-medium leading-snug line-clamp-2">{label}</p>
                      <div className="flex items-center gap-1.5 mt-1.5">
                        {vs ? (
                          <span className={`${vs.color} text-white text-[9px] font-black px-1.5 py-0.5 rounded-full`}>
                            {vs.label}
                          </span>
                        ) : (
                          <span className="text-[9px] text-brand-light">분석 중…</span>
                        )}
                        <span className="text-[9px] text-brand-light">{formatTime(h.timestamp)}</span>
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </aside>

      {/* ── 오른쪽 메인 영역 ── */}
      <div className="flex-1 h-full overflow-y-auto p-6 md:p-10">
      <div className="mb-8">
        {onBack && (
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 text-xs font-bold text-brand-muted hover:text-sky-500 transition-colors mb-4"
          >
            ← 홈으로
          </button>
        )}
        <h1 className="font-display text-2xl font-black tracking-tight text-brand-text">
          광고 시뮬레이터
        </h1>
        <p className="text-sm text-brand-muted mt-1">
          AI 페르소나가 실제 사람처럼 광고에 반응합니다 — 형식적인 AI 평가 없이.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="mb-10">
        <div className="bg-white border border-sky-400/20 rounded-2xl p-6 space-y-5 shadow-card">

          {/* ── 미디어 업로드 ── */}
          <div>
            <label className="block text-xs font-bold text-brand-muted uppercase tracking-widest mb-2">
              광고 미디어{" "}
              <span className="text-brand-light normal-case font-normal">(선택)</span>
            </label>

            {!mediaFile ? (
              <div
                className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer ${
                  dragOver
                    ? "border-sky-400 bg-sky-50"
                    : "border-sky-400/25 hover:border-sky-400/50 bg-brand-bg"
                }`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="text-3xl mb-2">📎</div>
                <p className="text-sm text-brand-muted">
                  이미지 또는 영상을 드래그하거나 클릭해서 업로드
                </p>
                <p className="text-xs text-brand-light mt-1">
                  이미지: JPG·PNG·GIF·WEBP (최대 10MB) &nbsp;|&nbsp; 영상: MP4·MOV·AVI·WEBM (최대 50MB)
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPTED_ALL.join(",")}
                  className="hidden"
                  onChange={handleFileInput}
                  disabled={loading}
                />
              </div>
            ) : (
              <div className="relative rounded-xl overflow-hidden border border-sky-400/20">
                {isVideo ? (
                  <video src={previewUrl} controls className="w-full max-h-64 object-contain bg-brand-text" />
                ) : (
                  <img src={previewUrl} alt="미리보기" className="w-full max-h-64 object-contain bg-brand-bg" />
                )}
                <div className="flex items-center gap-2 px-3 py-2 bg-white border-t border-sky-400/15">
                  <span className="text-xs text-brand-muted truncate flex-1">{mediaFile.name}</span>
                  <span className="text-xs text-brand-light shrink-0">{formatFileSize(mediaFile.size)}</span>
                  <button
                    type="button"
                    onClick={removeMedia}
                    disabled={loading}
                    className="text-xs text-brand-light hover:text-red-500 transition-colors shrink-0 ml-1"
                  >
                    ✕ 제거
                  </button>
                </div>
              </div>
            )}

            {fileError && (
              <p className="text-xs text-red-500 mt-1.5">{fileError}</p>
            )}
          </div>

          {/* ── 광고 텍스트 ── */}
          <div>
            <label className="block text-xs font-bold text-brand-muted uppercase tracking-widest mb-2">
              광고 내용{" "}
              <span className="text-brand-light normal-case font-normal">
                {mediaFile ? "(선택 — 미디어에 텍스트 보완 가능)" : "(필수 — 최소 10자)"}
              </span>
            </label>
            <textarea
              className="w-full bg-brand-bg border border-sky-400/20 rounded-xl p-3.5 text-sm text-brand-text
                         placeholder-brand-light focus:outline-none focus:border-sky-400 focus:bg-white
                         focus:shadow-[0_0_0_3px_rgba(56,189,248,0.12)] resize-none transition-all"
              rows={4}
              placeholder={
                mediaFile
                  ? "헤드라인, CTA, 추가 설명을 입력하면 AI가 미디어와 함께 분석합니다 (생략 가능)"
                  : `광고를 자세히 설명해 주세요:\n- 헤드라인\n- 본문 내용\n- CTA 문구\n- 비주얼 / 형식 설명`
              }
              value={adContent}
              onChange={(e) => setAdContent(e.target.value)}
              disabled={loading}
            />
          </div>

          {/* ── 광고 유형 + 버튼 ── */}
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-xs font-bold text-brand-muted uppercase tracking-widest mb-2">
                광고 유형
              </label>
              <div className="flex gap-2">
                {AD_TYPE_OPTIONS.map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setAdType(t)}
                    className={`text-xs px-3 py-1.5 rounded-full font-bold border transition-all ${
                      adType === t
                        ? "bg-sky-400 border-sky-400 text-white shadow-[0_3px_10px_rgba(56,189,248,0.28)]"
                        : "bg-white border-sky-400/20 text-brand-muted hover:border-sky-400/50 hover:bg-sky-50 hover:text-sky-600"
                    }`}
                  >
                    {AD_TYPE_LABELS[t]}
                  </button>
                ))}
              </div>
            </div>

            <div className="ml-auto flex gap-3">
              {displayedResult && (
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-4 py-2 text-sm font-bold text-brand-muted border border-sky-400/20 bg-white rounded-xl hover:border-sky-400/40 hover:text-sky-500 transition-colors"
                >
                  초기화
                </button>
              )}
              <div className="flex flex-col items-end gap-1">
                <button
                  type="submit"
                  disabled={!canSubmit}
                  className="px-6 py-2 bg-gradient-to-r from-sky-400 to-sky-500 hover:from-sky-500 hover:to-sky-600
                             disabled:from-brand-bg2 disabled:to-brand-bg2 disabled:text-brand-light
                             text-sm font-bold text-white rounded-xl transition-all
                             shadow-[0_4px_14px_rgba(56,189,248,0.28)] hover:shadow-[0_8px_22px_rgba(56,189,248,0.35)]
                             hover:-translate-y-0.5 active:translate-y-0"
                >
                  {loading ? "시뮬레이션 중…" : "시뮬레이션 실행"}
                </button>
                {!loading && activeCount === 0 && personas.length > 0 && (
                  <p className="text-[11px] text-amber-600">활성화된 페르소나를 1명 이상 선택해 주세요.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </form>

      {/* ── 내 페르소나 섹션 ── */}
      <div className="mb-10 flex items-center justify-between bg-white border border-sky-400/20 rounded-2xl px-5 py-3.5 shadow-card">
        <div className="flex items-center gap-3">
          <h2 className="text-xs font-bold text-brand-muted uppercase tracking-widest">내 페르소나</h2>
          {personas.length === 0 ? (
            <span className="text-xs text-brand-light">등록된 페르소나가 없습니다</span>
          ) : (
            <span className={`text-sm font-bold ${activeCount === 0 ? "text-amber-500" : "text-sky-500"}`}>
              {activeCount}명 선택됨 / {personas.length}명
            </span>
          )}
          {activeCount === 0 && personas.length > 0 && (
            <span className="text-[11px] text-amber-600">1명 이상 선택해 주세요</span>
          )}
        </div>
        <button
          onClick={onManagePersonas}
          className="text-xs font-bold text-sky-500 hover:text-sky-600 border border-sky-400/30 rounded-lg px-3 py-1.5 hover:bg-sky-50 transition-colors shrink-0"
        >
          페르소나 관리 →
        </button>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <div className="w-10 h-10 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-brand-muted">AI 페르소나들이 광고에 반응하는 중…</p>
          <p className="text-xs text-brand-light">
            (캐스케이드 파이프라인: 페르소나 선행 스크리닝 후 전체 실행)
          </p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-sm text-red-600">
          <span className="font-bold">시뮬레이션 실패: </span>{error}
        </div>
      )}

      {displayedResult && !loading && (
        <div className="space-y-8">
          <section>
            <SectionLabel>핵심 성과 지표</SectionLabel>
            <MetricsPanel metrics={displayedResult.metrics} />
          </section>

          <section>
            <SectionLabel>3단계 인지 퍼널</SectionLabel>
            <CognitiveTimeline metrics={displayedResult.metrics} totalPersonas={displayedResult.totalPersonas} />
          </section>

          <section>
            <SectionLabel>
              1단계 주요 키워드&nbsp;
              <span className="text-brand-light font-normal text-xs">(전체 페르소나 빈도)</span>
            </SectionLabel>
            <KeywordFrequency results={displayedResult.results} />
          </section>

          <section>
            <SectionLabel>
              페르소나별 인지 루프&nbsp;
              <span className="text-brand-light font-normal text-xs">
                ({displayedResult.totalPersonas}명)
              </span>
            </SectionLabel>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {displayedResult.results.map((r) => (
                <PersonaFeedbackCard key={r.personaId} result={r} persona={null} />
              ))}
            </div>
          </section>

          {displayedResult.conclusion && (
            <section>
              <SectionLabel>종합 결론</SectionLabel>
              <ConclusionPanel conclusion={displayedResult.conclusion} />
            </section>
          )}
        </div>
      )}
      </div>
    </div>
  );
}

function SectionLabel({ children }) {
  return (
    <h2 className="text-xs font-bold text-brand-muted uppercase tracking-widest mb-3">
      {children}
    </h2>
  );
}

const VERDICT_STYLE = {
  "집행 권장":     { bg: "bg-emerald-50", border: "border-emerald-300", badge: "bg-emerald-500", text: "text-emerald-700" },
  "수정 후 재검토": { bg: "bg-amber-50",   border: "border-amber-300",   badge: "bg-amber-500",   text: "text-amber-700"   },
  "집행 비권장":   { bg: "bg-red-50",     border: "border-red-300",     badge: "bg-red-500",     text: "text-red-700"     },
};

function ConclusionPanel({ conclusion }) {
  const style = VERDICT_STYLE[conclusion.verdict] ?? VERDICT_STYLE["수정 후 재검토"];

  return (
    <div className={`border ${style.border} ${style.bg} rounded-xl p-6 shadow-card space-y-4`}>
      <div className="flex items-center gap-3">
        <span className={`${style.badge} text-white text-sm font-black px-4 py-1.5 rounded-full tracking-wide`}>
          {conclusion.verdict}
        </span>
      </div>

      <p className={`text-sm leading-relaxed ${style.text} font-medium`}>{conclusion.reason}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
        {conclusion.strengths?.length > 0 && (
          <div>
            <p className="text-xs font-bold text-emerald-600 uppercase tracking-widest mb-2">강점</p>
            <ul className="space-y-1.5">
              {conclusion.strengths.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-brand-text">
                  <span className="text-emerald-500 mt-0.5 shrink-0">✓</span>
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}
        {conclusion.weaknesses?.length > 0 && (
          <div>
            <p className="text-xs font-bold text-red-500 uppercase tracking-widest mb-2">약점</p>
            <ul className="space-y-1.5">
              {conclusion.weaknesses.map((w, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-brand-text">
                  <span className="text-red-400 mt-0.5 shrink-0">✗</span>
                  {w}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function KeywordFrequency({ results }) {
  const sorted = useMemo(() => {
    const freq = {};
    for (const r of results) {
      for (const kw of (r.emotions ?? [])) {
        freq[kw.toLowerCase()] = (freq[kw.toLowerCase()] ?? 0) + 1;
      }
    }
    return Object.entries(freq)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 12);
  }, [results]);

  const max = sorted[0]?.[1] ?? 1;

  return (
    <div className="bg-white border border-sky-400/20 rounded-xl p-6 shadow-card">
      <div className="space-y-2.5">
        {sorted.map(([kw, count]) => (
          <div key={kw} className="flex items-center gap-3">
            <span className="text-sm text-brand-text w-32 truncate font-medium">{kw}</span>
            <div className="flex-1 h-2.5 bg-brand-bg2 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-sky-400 to-sky-500 rounded-full"
                style={{ width: `${(count / max) * 100}%` }}
              />
            </div>
            <span className="text-xs text-brand-muted tabular-nums w-6 text-right font-bold">
              {count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
