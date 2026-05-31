/**
 * Top KPI bar — 4 metric cards: VTR, CTR, Dropout, Avg Appeal.
 * Color thresholds are calibrated against industry benchmarks defined in AdProject.md.
 */
export default function MetricsPanel({ metrics }) {
  const cards = [
    {
      label: "VTR",
      sublabel: "View-Through Rate",
      value: `${metrics.vtr}%`,
      good: metrics.vtr >= 25,
      tip: "≥ 25% avg  |  ≥ 35% = great",
    },
    {
      label: "CTR",
      sublabel: "Click-Through Rate",
      value: `${metrics.ctr}%`,
      good: metrics.ctr >= 1.5,
      tip: "≥ 1.5% avg  |  ≥ 3% = great",
    },
    {
      label: "DROP",
      sublabel: "Step-2 Dropout Rate",
      value: `${metrics.dropoutRate}%`,
      good: metrics.dropoutRate < 70,
      invert: true,
      tip: "< 70% = acceptable",
    },
    {
      label: "APPEAL",
      sublabel: "Avg Gut-Feel Score",
      value: `${metrics.avgAppealScore} / 5`,
      good: metrics.avgAppealScore >= 3,
      tip: "≥ 3.0 avg  |  ≥ 4.0 = great",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((c) => (
        <div
          key={c.label}
          className="bg-gray-900 border border-gray-700 rounded-xl p-5 flex flex-col gap-1"
        >
          <span className="text-xs font-semibold tracking-widest text-gray-500 uppercase">
            {c.sublabel}
          </span>
          <span
            className={`text-3xl font-black tabular-nums ${
              c.good ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {c.value}
          </span>
          <span className="text-xs text-gray-600 mt-1">{c.tip}</span>
        </div>
      ))}
    </div>
  );
}
