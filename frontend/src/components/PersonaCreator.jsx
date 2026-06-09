'use client';

import { useState } from "react";

const PLATFORMS = ["Instagram", "YouTube", "TikTok", "Facebook", "카카오", "네이버"];

const INPUT_CLS =
  "w-full bg-brand-bg border border-sky-400/20 rounded-lg px-3 py-2 text-sm text-brand-text " +
  "placeholder-brand-light focus:outline-none focus:border-sky-400 focus:bg-white transition-colors";

const LABEL_CLS = "block text-[11px] font-bold text-brand-muted uppercase tracking-widest mb-1";

function PersonaForm({ onSave, onCancel, initialData = null }) {
  const isEditing = initialData !== null;

  const [form, setForm] = useState({
    name: initialData?.name ?? "",
    age: initialData?.age ?? 25,
    job: initialData?.job ?? "",
    gender: initialData?.gender ?? "",
    platform: initialData?.platform ?? "Instagram",
    emotional_state: initialData?.emotional_state ?? "",
    context: initialData?.context ?? "",
    drop_off_trigger: initialData?.drop_off_trigger ?? "",
    interests: initialData?.interests?.join(", ") ?? "",
    deal_prone_score: initialData?.deal_prone_score ?? 0.5,
    brand_loyalty: initialData?.brand_loyalty ?? 0.5,
    price_threshold: initialData?.price_threshold ?? 50000,
    purchase_pattern: initialData?.purchase_pattern ?? "",
  });

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const setNum = (k) => (e) => setForm((f) => ({ ...f, [k]: Number(e.target.value) }));

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      persona_id: initialData?.persona_id ?? crypto.randomUUID(),
      name: form.name,
      age: Number(form.age),
      job: form.job,
      gender: form.gender || null,
      platform: form.platform || null,
      emotional_state: form.emotional_state || null,
      context: form.context,
      drop_off_trigger: form.drop_off_trigger,
      interests: form.interests.split(",").map((s) => s.trim()).filter(Boolean),
      deal_prone_score: Number(form.deal_prone_score),
      brand_loyalty: Number(form.brand_loyalty),
      price_threshold: Number(form.price_threshold),
      purchase_pattern: form.purchase_pattern || null,
    });
  };

  return (
    <div className="bg-white border border-sky-400/20 rounded-2xl p-6 shadow-card">
      <p className="text-xs font-black uppercase tracking-widest text-brand-muted mb-4">
        {isEditing ? `${initialData.name} 수정` : "새 페르소나 만들기"}
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* 기본 정보 */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={LABEL_CLS}>이름 *</label>
            <input required value={form.name} onChange={set("name")}
              placeholder="예: 김지은" className={INPUT_CLS} />
          </div>
          <div>
            <label className={LABEL_CLS}>나이 *</label>
            <input required type="number" min={13} max={80}
              value={form.age} onChange={setNum("age")} className={INPUT_CLS} />
          </div>
          <div>
            <label className={LABEL_CLS}>직업 *</label>
            <input required value={form.job} onChange={set("job")}
              placeholder="예: 프리랜서 디자이너" className={INPUT_CLS} />
          </div>
          <div>
            <label className={LABEL_CLS}>성별</label>
            <select value={form.gender} onChange={set("gender")} className={INPUT_CLS}>
              <option value="">선택 안 함</option>
              <option value="male">남성</option>
              <option value="female">여성</option>
            </select>
          </div>
        </div>

        {/* 플랫폼 & 감정 상태 */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={LABEL_CLS}>플랫폼</label>
            <select value={form.platform} onChange={set("platform")} className={INPUT_CLS}>
              {PLATFORMS.map((p) => <option key={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className={LABEL_CLS}>감정 상태</label>
            <input value={form.emotional_state} onChange={set("emotional_state")}
              placeholder="예: 피곤함, 설렘" className={INPUT_CLS} />
          </div>
        </div>

        {/* 상황 & 이탈 조건 */}
        <div>
          <label className={LABEL_CLS}>현재 상황 *</label>
          <textarea required value={form.context} onChange={set("context")}
            placeholder="예: 점심시간에 인스타 피드를 스크롤하는 중"
            rows={2} className={INPUT_CLS + " resize-none"} />
        </div>
        <div>
          <label className={LABEL_CLS}>이탈 조건 *</label>
          <textarea required value={form.drop_off_trigger} onChange={set("drop_off_trigger")}
            placeholder="예: 가격이 비싸거나 관심 없는 카테고리면 바로 넘김"
            rows={2} className={INPUT_CLS + " resize-none"} />
        </div>

        {/* 관심사 */}
        <div>
          <label className={LABEL_CLS}>관심사</label>
          <input value={form.interests} onChange={set("interests")}
            placeholder="쉼표로 구분: 패션, 맛집, 운동" className={INPUT_CLS} />
        </div>

        {/* 구매 성향 슬라이더 */}
        <div className="space-y-3 pt-1">
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className={LABEL_CLS + " mb-0"}>가격 민감도</span>
              <span className="text-xs font-bold text-sky-500">{form.deal_prone_score}</span>
            </div>
            <input type="range" min="0" max="1" step="0.1"
              value={form.deal_prone_score} onChange={setNum("deal_prone_score")}
              className="w-full accent-sky-400" />
          </div>
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className={LABEL_CLS + " mb-0"}>팬덤</span>
              <span className="text-xs font-bold text-sky-500">{form.brand_loyalty}</span>
            </div>
            <input type="range" min="0" max="1" step="0.1"
              value={form.brand_loyalty} onChange={setNum("brand_loyalty")}
              className="w-full accent-sky-400" />
          </div>
          <div>
            <label className={LABEL_CLS}>최대 예산 (원)</label>
            <input type="number" min={0} value={form.price_threshold}
              onChange={setNum("price_threshold")} className={INPUT_CLS} />
          </div>
        </div>

        {/* 버튼 */}
        <div className="flex gap-3 pt-2">
          <button type="button" onClick={onCancel}
            className="flex-1 px-4 py-2 text-sm font-bold text-brand-muted border border-sky-400/20 bg-white rounded-xl hover:border-sky-400/40 hover:text-sky-500 transition-colors">
            취소
          </button>
          <button type="submit"
            className="flex-1 px-4 py-2 bg-gradient-to-r from-sky-400 to-sky-500 text-white text-sm font-bold rounded-xl shadow-[0_4px_14px_rgba(56,189,248,0.28)] hover:from-sky-500 hover:to-sky-600 transition-all">
            {isEditing ? "수정 완료" : "저장"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default function PersonaManagerPage({ personas, activeIds, onAdd, onDelete, onToggle, onSetActiveIds, onUpdate, onBack, onGoSimulate }) {
  const [showForm, setShowForm] = useState(false);
  const [editingPersona, setEditingPersona] = useState(null);

  const handleSave = (persona) => {
    if (editingPersona) {
      onUpdate(persona);
    } else {
      onAdd(persona);
    }
    setShowForm(false);
    setEditingPersona(null);
  };

  const handleEdit = (p) => {
    setEditingPersona(p);
    setShowForm(true);
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingPersona(null);
  };

  const activeCount = personas.filter((p) => activeIds.has(p.persona_id)).length;

  return (
    <div className="min-h-screen bg-brand-bg p-6">
      <div className="max-w-2xl mx-auto">

        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <button
              onClick={onBack}
              className="flex items-center gap-1.5 text-xs font-bold text-brand-muted hover:text-sky-500 transition-colors mb-3"
            >
              ← 홈으로
            </button>
            <h1 className="font-display text-2xl font-black tracking-tight text-brand-text">
              내 페르소나
            </h1>
            <p className="text-sm text-brand-muted mt-1">
              체크된 페르소나만 시뮬레이션에 참여합니다 · 이 브라우저에만 저장됩니다
            </p>
          </div>
          <div className="flex flex-col items-end gap-2 mt-8">
            <button
              onClick={onGoSimulate}
              className="shrink-0 px-4 py-2 bg-gradient-to-r from-sky-400 to-sky-500 text-white text-sm font-bold rounded-xl shadow-[0_4px_14px_rgba(56,189,248,0.28)] hover:from-sky-500 hover:to-sky-600 transition-all hover:-translate-y-0.5"
            >
              시뮬레이션 시작 →
            </button>
          </div>
        </div>

        {/* Persona list */}
        <div className="mb-6">
          {personas.length === 0 ? (
            <div className="bg-white border border-dashed border-sky-400/25 rounded-2xl p-10 text-center">
              <div className="text-4xl mb-3">👤</div>
              <p className="text-sm font-bold text-brand-muted">아직 만든 페르소나가 없습니다</p>
              <p className="text-xs text-brand-light mt-1">
                페르소나를 추가하면 시뮬레이션에서 실제 사람처럼 광고에 반응합니다
              </p>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-2">
                <p className="text-[11px] text-brand-light">
                  총 {personas.length}명 · {activeCount}명 활성화
                </p>
                <button
                  onClick={() => {
                    const allActive = personas.every((p) => activeIds.has(p.persona_id));
                    onSetActiveIds(allActive ? new Set() : new Set(personas.map((p) => p.persona_id)));
                  }}
                  className="text-[11px] font-bold text-sky-500 hover:text-sky-600 transition-colors"
                >
                  {personas.every((p) => activeIds.has(p.persona_id)) ? '전체 해제' : '전체 선택'}
                </button>
              </div>
              <div className="bg-white border border-sky-400/20 rounded-2xl shadow-card divide-y divide-sky-400/10">
                {personas.map((p) => {
                  const checked = activeIds.has(p.persona_id);
                  return (
                    <div
                      key={p.persona_id}
                      className={`flex items-center gap-3 px-4 py-3.5 hover:bg-brand-bg transition-colors ${checked ? '' : 'opacity-50'}`}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => onToggle(p.persona_id)}
                        className="w-4 h-4 accent-sky-400 shrink-0 cursor-pointer"
                      />
                      <div
                        className="flex-1 min-w-0 cursor-pointer"
                        onClick={() => onToggle(p.persona_id)}
                      >
                        <p className="text-sm font-bold text-brand-text truncate">
                          {p.name}
                          <span className="ml-1.5 text-xs font-normal text-brand-muted">
                            {p.age}세 · {p.job}
                          </span>
                          {checked && (
                            <span className="ml-2 text-[10px] font-black text-sky-500 bg-sky-50 border border-sky-400/30 px-1.5 py-0.5 rounded-full">
                              활성
                            </span>
                          )}
                        </p>
                        <p className="text-[11px] text-brand-light truncate mt-0.5">
                          {p.platform && <span className="mr-1.5">{p.platform}</span>}
                          {p.context}
                        </p>
                        {p.interests?.length > 0 && (
                          <p className="text-[10px] text-brand-light truncate mt-0.5">
                            관심사: {p.interests.join(', ')}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={() => handleEdit(p)}
                        className="text-xs text-brand-light hover:text-sky-500 transition-colors shrink-0 px-2 py-1 rounded hover:bg-sky-50"
                      >
                        수정
                      </button>
                      <button
                        onClick={() => onDelete(p.persona_id)}
                        className="text-xs text-brand-light hover:text-red-400 transition-colors shrink-0 ml-1 px-2 py-1 rounded hover:bg-red-50"
                      >
                        삭제
                      </button>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>

        {/* Add button (always visible) */}
        <button
          onClick={() => setShowForm(true)}
          className="w-full py-3 border-2 border-dashed border-sky-400/30 rounded-2xl text-sm font-bold text-sky-500 hover:border-sky-400/60 hover:bg-sky-50 transition-all"
        >
          + 새 페르소나 추가
        </button>

      </div>

      {/* Modal */}
      {showForm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          onClick={handleCancel}
        >
          <div
            className="w-full max-w-lg max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <PersonaForm
              onSave={handleSave}
              onCancel={handleCancel}
              initialData={editingPersona}
            />
          </div>
        </div>
      )}
    </div>
  );
}
