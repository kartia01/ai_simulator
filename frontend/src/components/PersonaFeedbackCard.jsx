const ACTION_BADGE = {
  clicked: { className: "bg-emerald-900 text-emerald-300", label: "✓ 클릭" },
  dropped: { className: "bg-rose-900 text-rose-300",    label: "✗ 이탈" },
  ignored: { className: "bg-gray-700 text-gray-300",    label: "– 무시" },
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
          className={`w-3 h-3 rounded-full ${n <= score ? "bg-indigo-400" : "bg-gray-700"}`}
        />
      ))}
      <span className="text-xs text-gray-500 ml-1">{score}/5</span>
    </div>
  );
}

export default function PersonaFeedbackCard({ result, persona }) {
  const { step1UnconsciousReaction, step2SelfishFiltering, step3FinalAction } = result;
  const dropped = step2SelfishFiltering.isDroppedOut;
  const clicked = step3FinalAction.clicked;
  const badge = getBadge(clicked, dropped);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl overflow-hidden">

      {/* ── Header ── */}
      <div className="px-4 py-3 bg-gray-800 flex items-center justify-between">
        <div>
          <span className="font-bold text-gray-100 text-sm">
            {persona?.name ?? result.personaId}
          </span>
          {persona && (
            <span className="text-xs text-gray-500 ml-2">
              {persona.age}세 · {persona.job}
            </span>
          )}
        </div>
        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${badge.className}`}>
          {badge.label}
        </span>
      </div>

      {/* ── Steps ── */}
      <div className="p-4 space-y-4">

        {/* Step 1 — 무의식적 반응 */}
        <div>
          <StepLabel step="1단계" title="무의식적 반응" color="text-indigo-400" />
          <div className="flex flex-wrap gap-2 mb-2">
            {step1UnconsciousReaction.keywords.map((kw, i) => (
              <span
                key={`${kw}-${i}`}
                className="bg-indigo-950 border border-indigo-800 text-indigo-300 text-xs px-2.5 py-1 rounded-full font-medium"
              >
                {kw}
              </span>
            ))}
          </div>
          <ScoreDots score={step1UnconsciousReaction.appealScore} />
        </div>

        {/* Step 2 — 자기중심적 필터링 */}
        <div>
          <StepLabel step="2단계" title="자기중심적 필터링" color="text-amber-400" />
          <blockquote
            className={`text-sm italic border-l-2 pl-3 ${
              dropped ? "border-rose-600 text-rose-300" : "border-emerald-600 text-emerald-300"
            }`}
          >
            "{step2SelfishFiltering.reason}"
          </blockquote>
        </div>

        {/* Step 3 — 최종 행동 */}
        <div>
          <StepLabel step="3단계" title="최종 행동" color="text-emerald-400" />
          <p className="text-sm text-gray-300">{step3FinalAction.actionReason}</p>
        </div>

        {persona?.context && (
          <p className="text-xs text-gray-600 border-t border-gray-800 pt-3">
            상황: {persona.context}
          </p>
        )}
      </div>

    </div>
  );
}
