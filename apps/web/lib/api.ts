const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? null;
const apiBaseUrl = configuredApiBaseUrl ?? "";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = {
    ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(init?.headers ?? {})
  };
  const baseUrls = Array.from(
    new Set([configuredApiBaseUrl, ""].filter((value): value is string => value !== null))
  );

  let networkError: Error | null = null;
  for (const baseUrl of baseUrls) {
    try {
      const response = await fetch(`${baseUrl}${path}`, {
        ...init,
        headers,
        cache: "no-store"
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || `Request failed: ${response.status}`);
      }

      return response.json() as Promise<T>;
    } catch (error) {
      if (!(error instanceof TypeError) || baseUrl === baseUrls[baseUrls.length - 1]) {
        throw error;
      }
      networkError = error;
    }
  }

  throw networkError ?? new Error("Failed to reach the Learnable API.");
}

export { apiBaseUrl };
