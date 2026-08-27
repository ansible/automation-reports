import {
  generatePKCE,
  storePKCEVerifier,
  getPKCEVerifier,
  clearPKCEVerifier,
} from '../../../src/frontend/app/utils/pkce';

describe('PKCE Utilities', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  describe('generatePKCE', () => {
    it('should generate a valid PKCE pair', async () => {
      const { verifier, challenge } = await generatePKCE();

      expect(verifier).toBeDefined();
      expect(challenge).toBeDefined();
      expect(typeof verifier).toBe('string');
      expect(typeof challenge).toBe('string');
    });

    it('code_verifier should be 43-128 characters', async () => {
      const { verifier } = await generatePKCE();
      expect(verifier.length).toBeGreaterThanOrEqual(43);
      expect(verifier.length).toBeLessThanOrEqual(128);
    });

    it('code_verifier should contain only unreserved characters', async () => {
      const { verifier } = await generatePKCE();
      // RFC 7636 unreserved: A-Z a-z 0-9 - . _ ~
      const unreservedRegex = /^[A-Za-z0-9\-._~]+$/;
      expect(unreservedRegex.test(verifier)).toBe(true);
    });

    it('code_challenge should not contain padding', async () => {
      const { challenge } = await generatePKCE();
      expect(challenge).not.toMatch(/=$/);
    });

    it('code_challenge should contain only base64url characters', async () => {
      const { challenge } = await generatePKCE();
      // base64url: A-Z a-z 0-9 - _
      const base64urlRegex = /^[A-Za-z0-9\-_]+$/;
      expect(base64urlRegex.test(challenge)).toBe(true);
    });

    it('should generate different pairs on each call', async () => {
      const pair1 = await generatePKCE();
      const pair2 = await generatePKCE();

      expect(pair1.verifier).not.toBe(pair2.verifier);
      expect(pair1.challenge).not.toBe(pair2.challenge);
    });

    it('code_challenge should be derived from code_verifier', async () => {
      const { verifier, challenge } = await generatePKCE();

      // Verify the challenge is correctly computed (SHA256 of verifier)
      const encoder = new TextEncoder();
      const data = encoder.encode(verifier);
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      const expectedChallenge = btoa(String.fromCodePoint(...new Uint8Array(hashBuffer)))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/={1,2}$/, '');

      expect(challenge).toBe(expectedChallenge);
    });
  });

  describe('storePKCEVerifier', () => {
    it('should store verifier in sessionStorage', () => {
      const verifier = 'test_verifier_value';
      storePKCEVerifier(verifier);

      expect(sessionStorage.getItem('pkce_verifier')).toBe(verifier);
    });

    it('should overwrite previous verifier', () => {
      storePKCEVerifier('first_verifier');
      storePKCEVerifier('second_verifier');

      expect(sessionStorage.getItem('pkce_verifier')).toBe('second_verifier');
    });
  });

  describe('getPKCEVerifier', () => {
    it('should retrieve verifier from sessionStorage', () => {
      const verifier = 'test_verifier_value';
      storePKCEVerifier(verifier);

      expect(getPKCEVerifier()).toBe(verifier);
    });

    it('should return null if verifier not stored', () => {
      expect(getPKCEVerifier()).toBeNull();
    });
  });

  describe('clearPKCEVerifier', () => {
    it('should remove verifier from sessionStorage', () => {
      storePKCEVerifier('test_verifier');
      expect(sessionStorage.getItem('pkce_verifier')).toBe('test_verifier');

      clearPKCEVerifier();
      expect(sessionStorage.getItem('pkce_verifier')).toBeNull();
    });

    it('should not throw if verifier not stored', () => {
      expect(() => clearPKCEVerifier()).not.toThrow();
    });
  });

  describe('PKCE flow integration', () => {
    it('should handle complete PKCE flow', async () => {
      // Generate PKCE pair
      const { verifier, challenge } = await generatePKCE();

      // Store verifier
      storePKCEVerifier(verifier);
      expect(getPKCEVerifier()).toBe(verifier);

      // Simulate auth redirect with challenge...
      // Later, retrieve and use verifier
      const retrievedVerifier = getPKCEVerifier();
      expect(retrievedVerifier).toBe(verifier);

      // Clear after use
      clearPKCEVerifier();
      expect(getPKCEVerifier()).toBeNull();
    });
  });
});
