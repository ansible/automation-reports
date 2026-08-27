import { expect, test, describe, vi, beforeEach } from 'vitest';

vi.mock('../../../src/frontend/app/client/apiClient', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

import { RestService } from '../../../src/frontend/app/Services/RestService';
import apiClient from '../../../src/frontend/app/client/apiClient';

const mockApi = apiClient as any;

describe('RestService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  describe('authorizeUser - PKCE Support', () => {
    test('should authorize without code_verifier (backward compatibility)', async () => {
      mockApi.post.mockResolvedValue({ data: { access_token: 'test-token' } });

      const authCode = 'test-auth-code';
      const callbackUri = 'http://localhost:9000/auth-callback';

      const result = await RestService.authorizeUser(authCode, callbackUri);

      expect(result).toEqual({ access_token: 'test-token' });
      expect(mockApi.post).toHaveBeenCalledWith(
        '/api/v1/aap_auth/token/',
        {
          auth_code: authCode,
          redirect_uri: callbackUri,
        }
      );
    });

    test('should include code_verifier when provided (PKCE)', async () => {
      mockApi.post.mockResolvedValue({ data: { access_token: 'test-token' } });

      const authCode = 'test-auth-code';
      const callbackUri = 'http://localhost:9000/auth-callback';
      const codeVerifier = 'test-pkce-verifier-that-is-at-least-43-characters-long';

      const result = await RestService.authorizeUser(authCode, callbackUri, codeVerifier);

      expect(result).toEqual({ access_token: 'test-token' });
      expect(mockApi.post).toHaveBeenCalledWith(
        '/api/v1/aap_auth/token/',
        {
          auth_code: authCode,
          redirect_uri: callbackUri,
          code_verifier: codeVerifier,
        }
      );
    });

    test('should not include code_verifier when null is passed', async () => {
      mockApi.post.mockResolvedValue({ data: { access_token: 'test-token' } });

      const authCode = 'test-auth-code';
      const callbackUri = 'http://localhost:9000/auth-callback';

      const result = await RestService.authorizeUser(authCode, callbackUri, null);

      expect(result).toEqual({ access_token: 'test-token' });
      expect(mockApi.post).toHaveBeenCalledWith(
        '/api/v1/aap_auth/token/',
        {
          auth_code: authCode,
          redirect_uri: callbackUri,
        }
      );
    });

    test('should handle authorization error without PKCE', async () => {
      const mockError = new Error('Invalid authorization code');
      mockApi.post.mockRejectedValue(mockError);

      const authCode = 'invalid-code';
      const callbackUri = 'http://localhost:9000/auth-callback';

      try {
        await RestService.authorizeUser(authCode, callbackUri);
        throw new Error('Should have thrown');
      } catch (error: any) {
        expect(error.message).toBe('Invalid authorization code');
      }
    });

    test('should handle authorization error with PKCE', async () => {
      const mockError = new Error('PKCE verification failed');
      mockApi.post.mockRejectedValue(mockError);

      const authCode = 'test-auth-code';
      const callbackUri = 'http://localhost:9000/auth-callback';
      const codeVerifier = 'invalid-verifier';

      try {
        await RestService.authorizeUser(authCode, callbackUri, codeVerifier);
        throw new Error('Should have thrown');
      } catch (error: any) {
        expect(error.message).toBe('PKCE verification failed');
      }
    });
  });

  describe('getMyUserData', () => {
    test('should fetch user data successfully', async () => {
      const mockUserData = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_staff: false,
      };
      const mockResponse = { data: mockUserData };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await RestService.getMyUserData();

      expect(result).toEqual(mockUserData);
      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/users/me/');
    });

    test('should handle user data fetch error', async () => {
      const mockError = new Error('Unauthorized');
      mockApi.get.mockRejectedValue(mockError);

      try {
        await RestService.getMyUserData();
        throw new Error('Should have thrown');
      } catch (error: any) {
        expect(error.message).toBe('Unauthorized');
      }
    });
  });

  describe('fetchAapSettings', () => {
    test('should fetch AAP settings successfully', async () => {
      const mockSettings = {
        name: 'Test AAP',
        url: 'https://aap.example.com',
        client_id: 'test-client-id',
        response_type: 'code',
        approval_prompt: 'auto',
      };
      const mockResponse = { data: mockSettings };
      mockApi.get.mockResolvedValue(mockResponse);

      const result = await RestService.fetchAapSettings();

      expect(result.data).toEqual(mockSettings);
      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/aap_auth/settings/');
    });

    test('should handle settings fetch error', async () => {
      const mockError = new Error('Settings not configured');
      mockApi.get.mockRejectedValue(mockError);

      try {
        await RestService.fetchAapSettings();
        throw new Error('Should have thrown');
      } catch (error: any) {
        expect(error.message).toBe('Settings not configured');
      }
    });
  });

  describe('logoutUser', () => {
    test('should logout user successfully', async () => {
      const mockResponse = { data: { message: 'Logged out' } };
      mockApi.post.mockResolvedValue(mockResponse);

      const result = await RestService.logoutUser();

      expect(result).toEqual({ message: 'Logged out' });
      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/aap_auth/logout/');
    });

    test('should handle logout error', async () => {
      const mockError = new Error('Logout failed');
      mockApi.post.mockRejectedValue(mockError);

      try {
        await RestService.logoutUser();
        throw new Error('Should have thrown');
      } catch (error: any) {
        expect(error.message).toBe('Logout failed');
      }
    });
  });

  describe('refreshAccessToken', () => {
    test('should refresh token successfully', async () => {
      const mockResponse = {
        data: {
          access_token: 'new-access-token',
          expires_in: 3600,
        },
      };
      mockApi.post.mockResolvedValue(mockResponse);

      const result = await RestService.refreshAccessToken();

      expect(result).toEqual({ access_token: 'new-access-token', expires_in: 3600 });
      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/aap_auth/refresh_token/', {});
    });

    test('should handle token refresh error', async () => {
      const mockError = new Error('Refresh failed');
      mockApi.post.mockRejectedValue(mockError);

      try {
        await RestService.refreshAccessToken();
        throw new Error('Should have thrown');
      } catch (error: any) {
        expect(error.message).toBe('Refresh failed');
      }
    });
  });

  describe('PKCE Verifier Length Constraints', () => {
    test('should accept 43-character verifier (minimum PKCE length)', async () => {
      mockApi.post.mockResolvedValue({ data: { access_token: 'test-token' } });

      const authCode = 'test-auth-code';
      const callbackUri = 'http://localhost:9000/auth-callback';
      const minVerifier = 'a'.repeat(43);

      await RestService.authorizeUser(authCode, callbackUri, minVerifier);

      expect(mockApi.post).toHaveBeenCalledWith(
        '/api/v1/aap_auth/token/',
        expect.objectContaining({
          code_verifier: minVerifier,
        })
      );
    });

    test('should accept 128-character verifier (maximum PKCE length)', async () => {
      mockApi.post.mockResolvedValue({ data: { access_token: 'test-token' } });

      const authCode = 'test-auth-code';
      const callbackUri = 'http://localhost:9000/auth-callback';
      const maxVerifier = 'a'.repeat(128);

      await RestService.authorizeUser(authCode, callbackUri, maxVerifier);

      expect(mockApi.post).toHaveBeenCalledWith(
        '/api/v1/aap_auth/token/',
        expect.objectContaining({
          code_verifier: maxVerifier,
        })
      );
    });
  });

  describe('Backward Compatibility', () => {
    test('should work without code_verifier parameter for older AAP versions', async () => {
      mockApi.post.mockResolvedValue({ data: { access_token: 'test-token' } });

      const authCode = 'test-auth-code';
      const callbackUri = 'http://localhost:9000/auth-callback';

      await RestService.authorizeUser(authCode, callbackUri);

      expect(mockApi.post).toHaveBeenCalledWith(
        '/api/v1/aap_auth/token/',
        {
          auth_code: authCode,
          redirect_uri: callbackUri,
        }
      );
    });

    test('should not break when code_verifier is explicitly null', async () => {
      mockApi.post.mockResolvedValue({ data: { access_token: 'test-token' } });

      const authCode = 'test-auth-code';
      const callbackUri = 'http://localhost:9000/auth-callback';

      await RestService.authorizeUser(authCode, callbackUri, null);

      const callPayload = mockApi.post.mock.calls[0][1];
      expect(callPayload).not.toHaveProperty('code_verifier');
    });
  });

  describe('Error Handling with PKCE', () => {
    test('should provide meaningful error on PKCE mismatch', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            error: 'invalid_request',
            error_description: 'PKCE code verifier invalid',
          },
        },
      };
      mockApi.post.mockRejectedValue(mockError);

      const authCode = 'test-auth-code';
      const callbackUri = 'http://localhost:9000/auth-callback';
      const wrongVerifier = 'wrong-verifier-value';

      try {
        await RestService.authorizeUser(authCode, callbackUri, wrongVerifier);
        throw new Error('Should have thrown');
      } catch (error: any) {
        expect(error.response?.status).toBe(400);
      }
    });

    test('should handle server errors during PKCE verification', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { error: 'Internal Server Error' },
        },
      };
      mockApi.post.mockRejectedValue(mockError);

      const authCode = 'test-auth-code';
      const callbackUri = 'http://localhost:9000/auth-callback';
      const codeVerifier = 'test-pkce-verifier-that-is-at-least-43-characters-long';

      try {
        await RestService.authorizeUser(authCode, callbackUri, codeVerifier);
        throw new Error('Should have thrown');
      } catch (error: any) {
        expect(error.response?.status).toBe(500);
      }
    });
  });
});
