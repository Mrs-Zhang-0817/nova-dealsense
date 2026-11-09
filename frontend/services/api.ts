const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
export async function checkHealth(signal: AbortSignal): Promise<boolean> {
  const response = await fetch(base + "/health", {signal, cache:"no-store"});
  return response.ok && (await response.json()).success === true;
}
