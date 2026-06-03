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

export default function SimulationDashboard() {
  const { result, loading, error, simulate, reset } = useSimulation();

  const [adContent, setAdContent] = useState("");
  const [adType, setAdType] = useState("IMAGE");
  const [mediaFile, setMediaFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [fileError, setFileError] = useState(null);
  const fileInputRef = useRef(null);

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
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  }, []);

  const handleFileInput = (e) => {
    handleFile(e.target.files?.[0]);
    e.target.value = "";
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  const removeMedia = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setMediaFile(null);
    setPreviewUrl(null);
    setFileError(null);
  };

  // previewUrl이 교체되거나 컴포넌트가 언마운트될 때 메모리 누수 방지
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const isVideo = useMemo(
    () => mediaFile != null && ACCEPTED_VIDEO.includes(mediaFile.type),
    [mediaFile],
  );

  const canSubmit = useMemo(
    () => !loading && (adContent.trim().length >= 10 || mediaFile != null),
    [loading, adContent, mediaFile],
  );

  const handleReset = useCallback(() => {
    reset();
    removeMedia();
    setAdContent("");
  }, [reset, removeMedia]);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    if (!canSubmit) return;
    simulate({
      adId: `ad-${Date.now()}`,
      adContent,
      adType,
      personaIds: [],
      mediaFile: mediaFile ?? undefined,
    });
  }, [canSubmit, simulate, adContent, adType, mediaFile]);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 md:p-10">
      <div className="mb-8">
        <h1 className="text-2xl font-black tracking-tight text-white">
          광고 시뮬레이터
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          AI 페르소나가 실제 사람처럼 광고에 반응합니다 — 형식적인 AI 평가 없이.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="mb-10">
        <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-5">

          {/* ── 미디어 업로드 영역 ── */}
          <div>
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
              광고 미디어 <span className="text-gray-600 normal-case font-normal">(선택)</span>
            </label>

            {!mediaFile ? (
              <div
                className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer
                  ${dragOver
                    ? "border-indigo-400 bg-indigo-950/30"
                    : "border-gray-700 hover:border-gray-500 bg-gray-800/40"
                  }`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="text-3xl mb-2">📎</div>
                <p className="text-sm text-gray-400">
                  이미지 또는 영상을 드래그하거나 클릭해서 업로드
                </p>
                <p className="text-xs text-gray-600 mt-1">
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
              <div className="relative rounded-xl overflow-hidden border border-gray-700 bg-gray-800">
                {isVideo ? (
                  <video
                    src={previewUrl}
                    controls
                    className="w-full max-h-64 object-contain bg-black"
                  />
                ) : (
                  <img
                    src={previewUrl}
                    alt="미리보기"
                    className="w-full max-h-64 object-contain bg-gray-900"
                  />
                )}
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-800 border-t border-gray-700">
                  <span className="text-xs text-gray-400 truncate flex-1">
                    {mediaFile.name}
                  </span>
                  <span className="text-xs text-gray-600 shrink-0">
                    {formatFileSize(mediaFile.size)}
                  </span>
                  <button
                    type="button"
                    onClick={removeMedia}
                    disabled={loading}
                    className="text-xs text-gray-500 hover:text-rose-400 transition-colors shrink-0 ml-1"
                  >
                    ✕ 제거
                  </button>
                </div>
              </div>
            )}

            {fileError && (
              <p className="text-xs text-rose-400 mt-1.5">{fileError}</p>
            )}
          </div>

          {/* ── 광고 텍스트 ── */}
          <div>
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
              광고 내용{" "}
              <span className="text-gray-600 normal-case font-normal">
                {mediaFile ? "(선택 — 미디어에 텍스트 보완 가능)" : "(필수 — 최소 10자)"}
              </span>
            </label>
            <textarea
              className="w-full bg-gray-800 border border-gray-600 rounded-lg p-3 text-sm text-gray-100
                         placeholder-gray-600 focus:outline-none focus:border-indigo-500 resize-none"
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
              <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
                광고 유형
              </label>
              <div className="flex gap-2">
                {AD_TYPE_OPTIONS.map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setAdType(t)}
                    className={`text-xs px-3 py-1.5 rounded-full font-bold border transition-colors ${
                      adType === t
                        ? "bg-indigo-600 border-indigo-500 text-white"
                        : "bg-gray-800 border-gray-600 text-gray-400 hover:border-gray-400"
                    }`}
                  >
                    {AD_TYPE_LABELS[t]}
                  </button>
                ))}
              </div>
            </div>

            <div className="ml-auto flex gap-3">
              {result && (
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-4 py-2 text-sm text-gray-400 border border-gray-600 rounded-lg hover:border-gray-400 transition-colors"
                >
                  초기화
                </button>
              )}
              <button
                type="submit"
                disabled={!canSubmit}
                className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500
                           text-sm font-bold rounded-lg transition-colors"
              >
                {loading ? "시뮬레이션 중…" : "시뮬레이션 실행"}
              </button>
            </div>
          </div>
        </div>
      </form>

      {loading && (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-500">AI 페르소나들이 광고에 반응하는 중…</p>
          <p className="text-xs text-gray-600">
            (캐스케이드 파이프라인: 페르소나 선행 스크리닝 후 전체 실행)
          </p>
        </div>
      )}

      {error && (
        <div className="bg-rose-950 border border-rose-700 rounded-xl p-5 text-sm text-rose-300">
          <span className="font-bold">시뮬레이션 실패: </span>{error}
        </div>
      )}

      {result && !loading && (
        <div className="space-y-8">
          <section>
            <SectionLabel>핵심 성과 지표</SectionLabel>
            <MetricsPanel metrics={result.metrics} />
          </section>

          <section>
            <SectionLabel>3단계 인지 퍼널</SectionLabel>
            <CognitiveTimeline
              metrics={result.metrics}
              totalPersonas={result.totalPersonas}
            />
          </section>

          <section>
            <SectionLabel>
              1단계 주요 키워드&nbsp;
              <span className="text-gray-600 font-normal text-xs">(전체 페르소나 빈도)</span>
            </SectionLabel>
            <KeywordFrequency results={result.results} />
          </section>

          <section>
            <SectionLabel>
              페르소나별 인지 루프&nbsp;
              <span className="text-gray-600 font-normal text-xs">
                ({result.totalPersonas}명)
              </span>
            </SectionLabel>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {result.results.map((r) => (
                <PersonaFeedbackCard
                  key={r.personaId}
                  result={r}
                  persona={null}
                />
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function SectionLabel({ children }) {
  return (
    <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">
      {children}
    </h2>
  );
}

function KeywordFrequency({ results }) {
  const freq = {};
  for (const r of results) {
    for (const kw of r.step1UnconsciousReaction.keywords) {
      freq[kw.toLowerCase()] = (freq[kw.toLowerCase()] ?? 0) + 1;
    }
  }

  const sorted = Object.entries(freq)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 12);

  const max = sorted[0]?.[1] ?? 1;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6">
      <div className="space-y-2">
        {sorted.map(([kw, count]) => (
          <div key={kw} className="flex items-center gap-3">
            <span className="text-sm text-gray-200 w-32 truncate">{kw}</span>
            <div className="flex-1 h-2.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-500 rounded-full"
                style={{ width: `${(count / max) * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-500 tabular-nums w-6 text-right">
              {count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
