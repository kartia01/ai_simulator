/**
 * Individual persona result card — shows the complete 3-step cognitive journey
 * for one simulated human. Marketers can read these to understand WHY the ad
 * succeeded or failed for each demographic slice.
 */
export default function PersonaFeedbackCard({ result, persona }) {
  const { step1UnconsciousReaction, step2SelfishFiltering, step3FinalAction } = result;
  const dropped = step2SelfishFiltering.isDroppedOut;
  const clicked = step3FinalAction.clicked;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl overflow-hidden">
      {/* Persona header */}
      <div className="px-4 py-3 bg-gray-800 flex items-center justify-between">
        <div>
          <span className="font-bold text-gray-100 text-sm">
            {persona?.name ?? result.personaId}
          </span>
          {persona && (
            <span className="text-xs text-gray-500 ml-2">
              {persona.age}y · {persona.job}
            </span>
          )}
        </div>
        {/* Final outcome badge */}
        <span
          className={`text-xs font-bold px-2.5 py-1 rounded-full ${
            clicked
              ? "bg-emerald-900 text-emerald-300"
              : dropped
              ? "bg-rose-900 text-rose-300"
              : "bg-gray-700 text-gray-300"
          }`}
        >
          {clicked ? "✓ CLICKED" : dropped ? "✗ DROPPED" : "– IGNORED"}
        </span>
      </div>

      <div className="p-4 space-y-4">
        {/* Step 1 */}
        <div>
          <p className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-2">
            Step 1 · Unconscious Reaction
          </p>
          <div className="flex flex-wrap gap-2 mb-2">
            {step1UnconsciousReaction.keywords.map((kw) => (
              <span
                key={kw}
                className="bg-indigo-950 border border-indigo-800 text-indigo-300 text-xs px-2.5 py-1 rounded-full font-medium"
              >
                {kw}
              </span>
            ))}
          </div>
          {/* Appeal score pips */}
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((n) => (
              <div
                key={n}
                className={`w-3 h-3 rounded-full ${
                  n <= step1UnconsciousReaction.appealScore
                    ? "bg-indigo-400"
                    : "bg-gray-700"
                }`}
              />
            ))}
            <span className="text-xs text-gray-500 ml-1">
              {step1UnconsciousReaction.appealScore}/5
            </span>
          </div>
        </div>

        {/* Step 2 */}
        <div>
          <p className="text-xs font-bold text-amber-400 uppercase tracking-widest mb-2">
            Step 2 · Selfish Filtering
          </p>
          <blockquote
            className={`text-sm italic border-l-2 pl-3 ${
              dropped
                ? "border-rose-600 text-rose-300"
                : "border-emerald-600 text-emerald-300"
            }`}
          >
            "{step2SelfishFiltering.reason}"
          </blockquote>
        </div>

        {/* Step 3 */}
        <div>
          <p className="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-2">
            Step 3 · Final Action
          </p>
          <p className="text-sm text-gray-300">
            {step3FinalAction.actionReason}
          </p>
        </div>

        {/* Context pill (if persona available) */}
        {persona?.context && (
          <p className="text-xs text-gray-600 border-t border-gray-800 pt-3">
            Context: {persona.context}
          </p>
        )}
      </div>
    </div>
  );
}
