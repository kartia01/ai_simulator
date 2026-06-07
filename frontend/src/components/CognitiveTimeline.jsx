export default function CognitiveTimeline({ metrics, totalPersonas }) {
  const stages = [
    {
      step: "1단계",
      label: "무의식적 반응",
      sub: "피드에서 광고 노출",
      pct: 100,
      count: totalPersonas,
      barClass: "bg-gradient-to-r from-sky-400 to-sky-500",
      text: "text-sky-500",
    },
    {
      step: "2단계",
      label: "페르소나의 속마음",
      sub: "이탈하지 않음",
      pct: metrics.vtr,
      count: Math.round((metrics.vtr / 100) * totalPersonas),
      barClass: "bg-gradient-to-r from-amber-400 to-amber-500",
      text: "text-amber-600",
    },
    {
      step: "3단계",
      label: "최종 행동",
      sub: "광고 클릭",
      pct: metrics.ctr,
      count: Math.round((metrics.ctr / 100) * totalPersonas),
      barClass: "bg-gradient-to-r from-emerald-400 to-emerald-500",
      text: "text-emerald-600",
    },
  ];

  return (
    <div className="bg-white border border-sky-400/20 rounded-xl p-6 shadow-card">
      <div className="space-y-5">
        {stages.map((s, i) => (
          <div key={s.step}>
            <div className="flex items-baseline justify-between mb-1.5">
              <div>
                <span className={`text-xs font-bold uppercase tracking-widest mr-2 ${s.text}`}>
                  {s.step}
                </span>
                <span className="text-sm font-semibold text-brand-text">{s.label}</span>
                <span className="text-xs text-brand-light ml-2">{s.sub}</span>
              </div>
              <div className="text-right tabular-nums">
                <span className={`text-xl font-black font-display ${s.text}`}>{s.pct}%</span>
                <span className="text-xs text-brand-light ml-1">({s.count}명)</span>
              </div>
            </div>

            <div className="h-3 bg-brand-bg2 rounded-full overflow-hidden">
              <div
                className={`h-full ${s.barClass} rounded-full transition-all duration-700`}
                style={{ width: `${s.pct}%` }}
              />
            </div>

            {i < stages.length - 1 && (
              <div className="mt-3 ml-2">
                <span className="text-xs text-brand-light">
                  ▼ {(stages[i].pct - stages[i + 1].pct).toFixed(1)}% 여기서 이탈
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-sky-400/10 flex items-center gap-3">
        <span className="text-xs text-brand-muted uppercase tracking-widest">
          1단계 평균 매력도
        </span>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((n) => (
            <div
              key={n}
              className={`w-5 h-5 rounded-sm ${
                n <= Math.round(metrics.avgAppealScore) ? "bg-sky-400" : "bg-brand-bg2"
              }`}
            />
          ))}
        </div>
        <span className="text-sm font-black font-display text-sky-500">
          {metrics.avgAppealScore} / 5
        </span>
      </div>
    </div>
  );
}
