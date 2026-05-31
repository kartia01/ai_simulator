const BASE_URL = process.env.REACT_APP_API_URL ?? "http://localhost:8080/api";

/**
 * POST /api/simulate
 * @param {{ adContent: string, adType: string, personaIds: string[] }} payload
 * @returns {Promise<SimulationResult>}
 */
export async function runSimulation(payload) {
  const res = await fetch(`${BASE_URL}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message ?? "Simulation failed");
  }

  return res.json();
}

/**
 * GET /api/personas
 * @returns {Promise<Persona[]>}
 */
export async function fetchPersonas() {
  const res = await fetch(`${BASE_URL}/personas`);
  if (!res.ok) throw new Error("Failed to load personas");
  return res.json();
}
