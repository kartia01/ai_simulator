const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export async function runSimulation(payload) {
  const { mediaFile, customPersonas, ...rest } = payload;

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
    if (customPersonas?.length) form.append("customPersonas", JSON.stringify(customPersonas));

    res = await fetch(`${BASE_URL}/simulate`, {
      method: "POST",
      body: form,
      // Content-Type은 설정하지 않음 — 브라우저가 boundary 포함해서 자동 설정
    });
  } else {
    res = await fetch(`${BASE_URL}/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...rest, customPersonas: customPersonas ?? [] }),
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

export async function createPersona(persona) {
  const res = await fetch(`${BASE_URL}/personas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(persona),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message ?? "페르소나 생성에 실패했습니다");
  }
  return res.json();
}

export async function updatePersona(persona) {
  const res = await fetch(`${BASE_URL}/personas/${persona.persona_id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(persona),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message ?? "페르소나 수정에 실패했습니다");
  }
  return res.json();
}

export async function deletePersona(id) {
  const res = await fetch(`${BASE_URL}/personas/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message ?? "페르소나 삭제에 실패했습니다");
  }
  return res.json();
}
