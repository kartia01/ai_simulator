export default function CognitiveTimeline({ metrics, totalPersonas }) {
  const stages = [
    {
      step: "1단계",
      label: "무의식적 반응",
      sub: "피드에서 광고 노출",
      pct: 100,
      count: totalPersonas,
      color: "bg-indigo-500",
      text: "text-indigo-300",
    },
    {
      step: "2단계",
      label: "페르소나의 속마음",
      sub: "이탈하지 않음",
      pct: metrics.vtr,
      count: Math.round((metrics.vtr / 100) * totalPersonas),
      color: "bg-amber-500",
      text: "text-amber-300",
    },
    {
      step: "3단계",
      label: "최종 행동",
      sub: "광고 클릭",
      pct: metrics.ctr,
      count: Math.round((metrics.ctr / 100) * totalPersonas),
      color: "bg-emerald-500",
      text: "text-emerald-300",
    },
  ];

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6">
      <h2 className="text-sm font-bold tracking-widest text-gray-400 uppercase mb-6">
        3단계 인지 퍼널
      </h2>

      <div className="space-y-5">
        {stages.map((s, i) => (
          <div key={s.step}>
            <div className="flex items-baseline justify-between mb-1.5">
              <div>
                <span className={`text-xs font-bold uppercase tracking-widest ${s.text} mr-2`}>
                  {s.step}
                </span>
                <span className="text-sm font-semibold text-gray-200">{s.label}</span>
                <span className="text-xs text-gray-500 ml-2">{s.sub}</span>
              </div>
              <div className="text-right tabular-nums">
                <span className={`text-xl font-black ${s.text}`}>{s.pct}%</span>
                <span className="text-xs text-gray-500 ml-1">({s.count}명)</span>
              </div>
            </div>

            <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full ${s.color} rounded-full transition-all duration-700`}
                style={{ width: `${s.pct}%` }}
              />
            </div>

            {i < stages.length - 1 && (
              <div className="flex items-center gap-2 mt-3 ml-2">
                <span className="text-gray-600 text-xs">
                  ▼ {(stages[i].pct - stages[i + 1].pct).toFixed(1)}% 여기서 이탈
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-800 flex items-center gap-3">
        <span className="text-xs text-gray-500 uppercase tracking-widest">
          1단계 평균 매력도
        </span>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((n) => (
            <div
              key={n}
              className={`w-5 h-5 rounded-sm ${
                n <= Math.round(metrics.avgAppealScore)
                  ? "bg-indigo-500"
                  : "bg-gray-700"
              }`}
            />
          ))}
        </div>
        <span className="text-sm font-bold text-indigo-300">
          {metrics.avgAppealScore} / 5
        </span>
      </div>
    </div>
  );
}
