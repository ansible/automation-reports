import { renderHook, act } from '@testing-library/react';
import { expect, test, describe, vi, beforeEach } from 'vitest';

vi.mock('../../../src/frontend/app/Services', () => ({
  RestService: {
    fetchAapSettings: vi.fn(),
    authorizeUser: vi.fn(),
    getMyUserData: vi.fn(),
    logoutUser: vi.fn(),
    refreshAccessToken: vi.fn(),
  },
}));

import { useAuthStore } from '../../../src/frontend/app/Store/authStore';
import { RestService } from '../../../src/frontend/app/Services';

describe('authStore', () => {
  const mockRestService = RestService as any;

  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({
      appSettings: null,
      myUserData: null,
      loading: 'idle',
      error: false,
      logErrorMessage: null,
    });
  });

  describe('fetchAppSettings', () => {
    test('should fetch and set app settings', async () => {
      const mockSettings = {
        data: {
          name: 'Test AAP',
          url: 'https://aap.example.com',
          client_id: 'test-client',
          response_type: 'code',
          approval_prompt: 'auto',
        },
      };

      mockRestService.fetchAapSettings.mockResolvedValue(mockSettings);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.fetchAppSettings();
      });

      expect(result.current.appSettings).toEqual(mockSettings.data);
      expect(result.current.loading).toBe('succeeded');
      expect(result.current.error).toBe(false);
    });

    test('should handle fetch error', async () => {
      mockRestService.fetchAapSettings.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.fetchAppSettings();
        } catch {
          // Expected error
        }
      });

      expect(result.current.appSettings).toBeNull();
      expect(result.current.loading).toBe('failed');
      expect(result.current.error).toBe(true);
    });
  });

  describe('authorizeUser with PKCE', () => {
    test('should authorize user without code_verifier', async () => {
      const mockUserData = { id: 1, username: 'testuser' };

      mockRestService.authorizeUser.mockResolvedValue({});
      mockRestService.getMyUserData.mockResolvedValue(mockUserData);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.authorizeUser('test-code');
      });

      expect(mockRestService.authorizeUser).toHaveBeenCalledWith(
        'test-code',
        expect.stringContaining('/auth-callback'),
        undefined
      );
      expect(result.current.myUserData).toEqual(mockUserData);
    });

    test('should authorize user with code_verifier (PKCE)', async () => {
      const mockUserData = { id: 1, username: 'testuser' };

      mockRestService.authorizeUser.mockResolvedValue({});
      mockRestService.getMyUserData.mockResolvedValue(mockUserData);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.authorizeUser('test-code', 'pkce-verifier');
      });

      expect(mockRestService.authorizeUser).toHaveBeenCalledWith(
        'test-code',
        expect.stringContaining('/auth-callback'),
        'pkce-verifier'
      );
      expect(result.current.myUserData).toEqual(mockUserData);
    });

    test('should handle authorization error with code_verifier', async () => {
      const error = new Error('Invalid PKCE');
      mockRestService.authorizeUser.mockRejectedValue(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.authorizeUser('test-code', 'invalid-verifier');
        } catch {
          // Expected error
        }
      });

      expect(result.current.loading).toBe('failed');
      expect(result.current.error).toBe(true);
    });

    test('should reject when no auth code provided', async () => {
      const { result } = renderHook(() => useAuthStore());
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await act(async () => {
        await result.current.authorizeUser('');
      });

      expect(consoleErrorSpy).toHaveBeenCalledWith('Authorization code is required');
      consoleErrorSpy.mockRestore();
    });
  });

  describe('getMyUserData', () => {
    test('should fetch user data', async () => {
      const mockUserData = { id: 1, username: 'testuser' };

      mockRestService.getMyUserData.mockResolvedValue(mockUserData);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.getMyUserData();
      });

      expect(result.current.myUserData).toEqual(mockUserData);
      expect(result.current.loading).toBe('succeeded');
    });

    test('should skip fetch if already has user data', async () => {
      const mockUserData = { id: 1, username: 'testuser' };

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        useAuthStore.setState({ myUserData: mockUserData });
      });

      mockRestService.getMyUserData.mockResolvedValue({});

      await act(async () => {
        await result.current.getMyUserData();
      });

      expect(mockRestService.getMyUserData).not.toHaveBeenCalled();
    });
  });

  describe('logout', () => {
    test('should clear user data and call logout', async () => {
      const mockUserData = { id: 1, username: 'testuser' };

      mockRestService.logoutUser.mockResolvedValue({});

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        useAuthStore.setState({ myUserData: mockUserData });
      });

      expect(result.current.isAuthenticated()).toBe(true);

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.myUserData).toBeNull();
      expect(result.current.isAuthenticated()).toBe(false);
    });
  });

  describe('refreshAccessToken', () => {
    test('should refresh token successfully', async () => {
      mockRestService.refreshAccessToken.mockResolvedValue({});

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.refreshAccessToken();
      });

      expect(result.current.loading).toBe('succeeded');
    });

    test('should handle refresh error', async () => {
      const error = new Error('Token refresh failed');
      mockRestService.refreshAccessToken.mockRejectedValue(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.refreshAccessToken();
        } catch {
          // Expected error
        }
      });

      expect(result.current.loading).toBe('failed');
    });
  });

  describe('isAuthenticated', () => {
    test('should return false when no user data', () => {
      const { result } = renderHook(() => useAuthStore());
      expect(result.current.isAuthenticated()).toBe(false);
    });

    test('should return true when user data exists', () => {
      const mockUserData = { id: 1, username: 'testuser' };

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        useAuthStore.setState({ myUserData: mockUserData });
      });

      expect(result.current.isAuthenticated()).toBe(true);
    });
  });

  describe('logError', () => {
    test('should set error message', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.logError('Test error message');
      });

      expect(result.current.logErrorMessage).toBe('Test error message');
    });
  });
});
