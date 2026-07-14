const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "::1", "[::1]"]);

function isPrivateIpv4(hostname: string) {
  const parts = hostname.split(".").map((part) => Number(part));
  if (parts.length !== 4 || parts.some((part) => !Number.isInteger(part) || part < 0 || part > 255)) {
    return false;
  }

  const [first, second] = parts;
  return (
    first === 10 ||
    first === 127 ||
    (first === 172 && second >= 16 && second <= 31) ||
    (first === 192 && second === 168)
  );
}

function isLocalDevHost(hostname: string) {
  return LOOPBACK_HOSTS.has(hostname) || isPrivateIpv4(hostname);
}

export function browserAwareBaseUrl(configuredUrl: string) {
  if (typeof window === "undefined" || !configuredUrl) return configuredUrl;

  try {
    const configured = new URL(configuredUrl);
    const browserHost = window.location.hostname;

    if (
      browserHost &&
      configured.hostname !== browserHost &&
      isLocalDevHost(configured.hostname) &&
      isLocalDevHost(browserHost)
    ) {
      configured.hostname = browserHost;
      return configured.toString().replace(/\/$/, "");
    }

    return configured.toString().replace(/\/$/, "");
  } catch {
    return configuredUrl;
  }
}
