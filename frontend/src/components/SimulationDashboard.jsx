import { useState } from "react";
import { useSimulation } from "../hooks/useSimulation";
import MetricsPanel from "./MetricsPanel";
import CognitiveTimeline from "./CognitiveTimeline";
import PersonaFeedbackCard from "./PersonaFeedbackCard";

const AD_TYPE_OPTIONS = ["IMAGE", "VIDEO", "CAROUSEL"];

export default function SimulationDashboard() {
  const { result, loading, error, simulate, reset } = useSimulation();

  const [adContent, setAdContent] = useState("");
  const [adType, setAdType] = useState("IMAGE");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!adContent.trim()) return;
    simulate({
      adId: `ad-${Date.now()}`,
      adContent,
      adType,
      personaIds: [],   // empty = use all personas from DB
    });
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 md:p-10">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-black tracking-tight text-white">
          Ad Simulator
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          AI personas react to your ad like real humans — no polite AI corporate mode.
        </p>
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit} className="mb-10">
        <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
              Ad Content
            </label>
            <textarea
              className="w-full bg-gray-800 border border-gray-600 rounded-lg p-3 text-sm text-gray-100
                         placeholder-gray-600 focus:outline-none focus:border-indigo-500 resize-none"
              rows={5}
              placeholder={`Describe your ad in full:\n- Headline\n- Body copy\n- CTA text\n- Visual / format description`}
              value={adContent}
              onChange={(e) => setAdContent(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="flex items-center gap-4">
            <div>
              <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
                Ad Type
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
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="ml-auto flex gap-3">
              {result && (
                <button
                  type="button"
                  onClick={reset}
                  className="px-4 py-2 text-sm text-gray-400 border border-gray-600 rounded-lg hover:border-gray-400 transition-colors"
                >
                  Reset
                </button>
              )}
              <button
                type="submit"
                disabled={loading || !adContent.trim()}
                className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500
                           text-sm font-bold rounded-lg transition-colors"
              >
                {loading ? "Simulating…" : "Run Simulation"}
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Loading state */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-500">
            AI personas are reacting to your ad…
          </p>
          <p className="text-xs text-gray-600">
            (Cascade pipeline: screening 3 personas first, then full batch)
          </p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-rose-950 border border-rose-700 rounded-xl p-5 text-sm text-rose-300">
          <span className="font-bold">Simulation failed: </span>{error}
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="space-y-8">
          {/* KPI metrics */}
          <section>
            <SectionLabel>Aggregate KPIs</SectionLabel>
            <MetricsPanel metrics={result.metrics} />
          </section>

          {/* Cognitive funnel */}
          <section>
            <SectionLabel>3-Step Cognitive Funnel</SectionLabel>
            <CognitiveTimeline
              metrics={result.metrics}
              totalPersonas={result.totalPersonas}
            />
          </section>

          {/* Top Keywords across all personas */}
          <section>
            <SectionLabel>
              Top Step-1 Keywords&nbsp;
              <span className="text-gray-600 font-normal text-xs">(frequency across all personas)</span>
            </SectionLabel>
            <KeywordFrequency results={result.results} />
          </section>

          {/* Per-persona cards */}
          <section>
            <SectionLabel>
              Per-Persona Cognitive Loops&nbsp;
              <span className="text-gray-600 font-normal text-xs">
                ({result.totalPersonas} personas)
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

// ── Sub-components ─────────────────────────────────────────────────────────────

function SectionLabel({ children }) {
  return (
    <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">
      {children}
    </h2>
  );
}

/**
 * Tallies Step-1 keywords across all personas and renders a ranked list.
 * No external library — just a sorted frequency map.
 */
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
