
export async function fetchServices() {
  try {
    const res = await fetch('/api/services/status');
    if (!res.ok) {
      throw new Error(`Ошибка HTTP: ${res.status}`);
    }
    return res.json();
  }
  catch (e: any) {
    console.error("Error fetching services:", e.message);
    return [];
  }
}


export async function fetchPrompts() {
  const res = await fetch("/api/prompts/list");
  return res.json();
}

export async function fetchConfig() {
  const res = await fetch('/api/config/list');
  return res.json();
}

export async function updatePrompt(data: {
  service: string;
  name: string;
  content: string;
}) {
  const res = await fetch("/api/prompts/update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.ok;
}

export async function sendProxyRequest(
  data: { service: string; method: string; endpoint: string; body?: any },
  isFile?: boolean
) {
  const options: RequestInit = {
    method: "POST",
    headers: {},
  };

  if (isFile) {
    // body уже FormData
    options.body = data.body;
    // НЕ устанавливаем Content-Type, браузер сам выставит multipart/form-data
  } else {
    options.body = JSON.stringify(data);
    options.headers = { "Content-Type": "application/json" };
  }

  const res = await fetch("/api/proxy", options);
  const result = await res.json();
  return result;
}


