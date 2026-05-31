import { useState, useCallback } from "react";
import { runSimulation } from "../api/simulationApi";

/**
 * Manages simulation state and exposes a `simulate` trigger.
 *
 * Returns:
 *  result    — SimulationResult | null
 *  loading   — boolean
 *  error     — string | null
 *  simulate  — (payload) => Promise<void>
 *  reset     — () => void
 */
export function useSimulation() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const simulate = useCallback(async (payload) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await runSimulation(payload);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, loading, error, simulate, reset };
}
