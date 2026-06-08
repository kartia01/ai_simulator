const ACTION_BADGE = {
  clicked: { className: "bg-emerald-100 text-emerald-700 border border-emerald-200", label: "✓ 클릭" },
  dropped: { className: "bg-red-100 text-red-600 border border-red-200",             label: "✗ 이탈" },
  ignored: { className: "bg-sky-50 text-brand-muted border border-sky-400/20",       label: "– 무시" },
};

function getBadge(clicked, dropped) {
  if (clicked) return ACTION_BADGE.clicked;
  if (dropped) return ACTION_BADGE.dropped;
  return ACTION_BADGE.ignored;
}

function StepLabel({ step, title, color }) {
  return (
    <p className={`text-xs font-bold uppercase tracking-widest mb-2 ${color}`}>
      {step} · {title}
    </p>
  );
}

function ScoreDots({ score }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((n) => (
        <div
          key={n}
          className={`w-3 h-3 rounded-full ${n <= score ? "bg-sky-400" : "bg-sky-100"}`}
        />
      ))}
      <span className="text-xs text-brand-light ml-1">{score}/5</span>
    </div>
  );
}

export default function PersonaFeedbackCard({ result, persona }) {
  const emotions = result.emotions ?? [];
  const appealScore = Math.round(result.attention * 4 + 1);
  const dropped = !result.clickIntent && result.sentiment < 0;
  const clicked = result.clickIntent;
  const badge = getBadge(clicked, dropped);

  return (
    <div className="bg-white border border-sky-400/20 rounded-xl overflow-hidden shadow-card">

      {/* ── Header ── */}
      <div className="px-4 py-3 bg-sky-50 border-b border-sky-400/15 flex items-center justify-between">
        <div>
          <span className="font-bold text-brand-text text-sm">
            {persona?.name ?? result.personaName ?? result.personaId}
          </span>
          <span className="text-xs text-brand-muted ml-2">
            {(persona?.age ?? result.personaAge)}세 · {(persona?.job ?? result.personaJob)}
          </span>

        </div>
        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${badge.className}`}>
          {badge.label}
        </span>
      </div>

      {/* ── Steps ── */}
      <div className="p-4 space-y-4">

        {/* Step 1 — 연상 단어 */}
        <div>
          <StepLabel step="1단계" title="연상 단어" color="text-sky-500" />
          <div className="flex flex-wrap gap-2 mb-2">
            {emotions.map((kw, i) => (
              <span
                key={`${kw}-${i}`}
                className="bg-sky-50 border border-sky-400/25 text-sky-600 text-xs px-2.5 py-1 rounded-full font-medium"
              >
                {kw}
              </span>
            ))}
          </div>
          <ScoreDots score={appealScore} />
        </div>

        {/* Step 2 — 속마음 */}
        <div>
          <StepLabel step="2단계" title="페르소나의 속마음" color="text-amber-600" />
          <blockquote
            className={`text-sm italic border-l-2 pl-3 ${
              dropped
                ? "border-red-300 text-red-600"
                : "border-emerald-300 text-emerald-700"
            }`}
          >
            "{result.reasoning ?? ""}"
          </blockquote>
        </div>

        {/* Step 3 — 느낀점 */}
        <div>
          <StepLabel step="3단계" title="느낀점" color="text-emerald-600" />
          <p className="text-sm text-brand-text">{result.impression ?? ""}</p>
        </div>

        {persona?.context && (
          <p className="text-xs text-brand-light border-t border-sky-400/10 pt-3">
            상황: {persona.context}
          </p>
        )}
      </div>

    </div>
  );
}
