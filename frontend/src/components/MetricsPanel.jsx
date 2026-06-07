export default function MetricsPanel({ metrics }) {
  const cards = [
    {
      label: "VTR",
      sublabel: "조회 완료율",
      value: `${metrics.vtr}%`,
      good: metrics.vtr >= 25,
      tip: "≥ 25% 평균  |  ≥ 35% = 우수",
    },
    {
      label: "CTR",
      sublabel: "클릭률",
      value: `${metrics.ctr}%`,
      good: metrics.ctr >= 1.5,
      tip: "≥ 1.5% 평균  |  ≥ 3% = 우수",
    },
    {
      label: "이탈",
      sublabel: "2단계 이탈률",
      value: `${metrics.dropoutRate}%`,
      good: metrics.dropoutRate < 70,
      tip: "< 70% = 허용 범위",
    },
    {
      label: "매력도",
      sublabel: "평균 직감 점수",
      value: `${metrics.avgAppealScore} / 5`,
      good: metrics.avgAppealScore >= 3,
      tip: "≥ 3.0 평균  |  ≥ 4.0 = 우수",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((c) => (
        <div
          key={c.label}
          className="bg-white border border-sky-400/20 rounded-xl p-5 flex flex-col gap-1 shadow-card"
        >
          <span className="text-xs font-bold tracking-widest text-brand-muted uppercase">
            {c.sublabel}
          </span>
          <span
            className={`text-3xl font-black tabular-nums font-display ${
              c.good ? "text-emerald-600" : "text-red-500"
            }`}
          >
            {c.value}
          </span>
          <span className="text-xs text-brand-light mt-1">{c.tip}</span>
        </div>
      ))}
    </div>
  );
}
