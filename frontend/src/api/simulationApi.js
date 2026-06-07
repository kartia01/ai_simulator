const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export async function runSimulation(payload) {
  const { mediaFile, ...rest } = payload;

  let res;
  if (mediaFile) {
    const form = new FormData();
    form.append("adId", rest.adId);
    form.append("adContent", rest.adContent ?? "");
    form.append("adType", rest.adType ?? "IMAGE");
    form.append("mediaFile", mediaFile);
    if (rest.objective) form.append("objective", rest.objective);
    if (rest.productPrice != null) form.append("productPrice", String(rest.productPrice));
    for (const pid of rest.personaIds ?? []) form.append("personaIds", pid);

    res = await fetch(`${BASE_URL}/simulate`, {
      method: "POST",
      body: form,
      // Content-Type은 설정하지 않음 — 브라우저가 boundary 포함해서 자동 설정
    });
  } else {
    res = await fetch(`${BASE_URL}/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(rest),
    });
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message ?? "시뮬레이션에 실패했습니다");
  }

  return res.json();
}

export async function fetchPersonas() {
  const res = await fetch(`${BASE_URL}/personas`);
  if (!res.ok) throw new Error("페르소나 목록을 불러오지 못했습니다");
  return res.json();
}
