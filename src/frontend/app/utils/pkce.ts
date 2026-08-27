/**
 * PKCE (Proof Key for Code Exchange) utilities for OAuth2 authorization flow.
 * Implements RFC 7636: https://tools.ietf.org/html/rfc7636
 */

/**
 * Generate a random PKCE code_verifier (43-128 characters, unreserved chars only).
 * Uses crypto.getRandomValues() for secure random generation.
 */
function generateCodeVerifier(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  // Base64-url encode without padding
  return btoa(String.fromCodePoint(...array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/={1,2}$/, '');
}

/**
 * Generate PKCE code_challenge from code_verifier using S256 method.
 * S256 = BASE64URL(SHA256(code_verifier))
 */
async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  // Convert ArrayBuffer to base64-url
  return btoa(String.fromCodePoint(...new Uint8Array(hashBuffer)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/={1,2}$/, '');
}

/**
 * Generate a PKCE pair (code_verifier, code_challenge).
 * Returns both values needed for the OAuth2 authorization flow.
 */
export async function generatePKCE(): Promise<{
  verifier: string;
  challenge: string;
}> {
  const verifier = generateCodeVerifier();
  const challenge = await generateCodeChallenge(verifier);
  return { verifier, challenge };
}

/**
 * Store PKCE verifier in sessionStorage.
 * Should be called immediately after generating PKCE pair and before redirect.
 */
export function storePKCEVerifier(verifier: string): void {
  sessionStorage.setItem('pkce_verifier', verifier);
}

/**
 * Retrieve PKCE verifier from sessionStorage.
 * Should be called in the auth callback to recover the verifier for token exchange.
 */
export function getPKCEVerifier(): string | null {
  return sessionStorage.getItem('pkce_verifier');
}

/**
 * Clear PKCE verifier from sessionStorage after use.
 * Should be called after successful token exchange.
 */
export function clearPKCEVerifier(): void {
  sessionStorage.removeItem('pkce_verifier');
}
