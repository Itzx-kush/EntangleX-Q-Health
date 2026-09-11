export type ApiLocation = {
  hostname?: string
  protocol?: string
}

/** Resolve the backend beside the frontend without hardcoding a LAN address. */
export function resolveApiBaseUrl(location: ApiLocation = globalThis.location): string {
  const configured = (globalThis as { ENTANGLEX_API_URL?: string }).ENTANGLEX_API_URL?.trim()
  if (configured) return configured.replace(/\/$/, "")
  const hostname = location.hostname === "localhost" ? "127.0.0.1" : (location.hostname || "127.0.0.1")
  const protocol = location.protocol === "https:" ? "https:" : "http:"
  return `${protocol}//${hostname}:8000`
}
