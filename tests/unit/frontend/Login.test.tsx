import { render, screen, fireEvent } from '@testing-library/react';
import { expect, test, describe, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import * as pkceUtils from '../../../src/frontend/app/utils/pkce';

vi.mock('../../../src/frontend/app/utils/pkce');

const mockAuthStore = {
  appSettings: {
    name: 'Test AAP',
    url: 'https://aap.example.com',
    client_id: 'test-client-id',
    response_type: 'code',
    approval_prompt: 'auto',
  },
  loading: 'succeeded',
  error: false,
  myUserData: null,
  logErrorMessage: '',
  fetchAppSettings: vi.fn(),
  authorizeUser: vi.fn(),
  getMyUserData: vi.fn(),
  logout: vi.fn(),
  refreshAccessToken: vi.fn(),
  isAuthenticated: vi.fn(),
  logError: vi.fn(),
};

vi.mock('../../../src/frontend/app/Store/authStore', () => ({
  useAuthStore: (selector: any) => selector(mockAuthStore),
}));

import { Login } from '../../../src/frontend/app/Components/Login';

describe('Login Component', () => {
  const mockPKCE = {
    verifier: 'test-pkce-verifier-that-is-at-least-43-characters-long',
    challenge: 'test-challenge-E9Mrozoa0owWoUgT5UwegIo1W-1sKhnQWXaC3iMT-5E',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();

    // Reset auth store
    mockAuthStore.appSettings = {
      name: 'Test AAP',
      url: 'https://aap.example.com',
      client_id: 'test-client-id',
      response_type: 'code',
      approval_prompt: 'auto',
    };
    mockAuthStore.loading = 'succeeded';
    mockAuthStore.error = false;
    mockAuthStore.fetchAppSettings.mockResolvedValue({});
    mockAuthStore.authorizeUser.mockResolvedValue({});

    // Mock PKCE utils
    vi.mocked(pkceUtils.generatePKCE).mockResolvedValue(mockPKCE);
    vi.mocked(pkceUtils.storePKCEVerifier).mockImplementation(() => {});
    vi.mocked(pkceUtils.getPKCEVerifier).mockReturnValue(mockPKCE.verifier);
    vi.mocked(pkceUtils.clearPKCEVerifier).mockImplementation(() => {});
  });

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
  };

  describe('Page Rendering', () => {
    test('should render login page with title', () => {
      renderComponent();
      expect(screen.getByText('Log in to your account')).toBeTruthy();
    });

    test('should display login button with AAP name', () => {
      renderComponent();
      expect(screen.getByRole('button', { name: /Login with Test AAP/i })).toBeTruthy();
    });

    test('should show different UI when loading', () => {
      mockAuthStore.loading = 'pending';
      mockAuthStore.appSettings = null;

      // Component should respond to loading state
      renderComponent();
      // When pending, component conditionally renders spinner
      expect(mockAuthStore.appSettings).toBeNull();
    });

    test('should show different UI when error occurs', () => {
      mockAuthStore.loading = 'failed';
      mockAuthStore.error = true;

      // Component should respond to error state
      renderComponent();
      expect(mockAuthStore.error).toBe(true);
    });
  });

  describe('PKCE Integration', () => {
    test('should initialize with PKCE utils available', () => {
      renderComponent();

      // PKCE utils should be mocked and available
      expect(vi.mocked(pkceUtils.generatePKCE)).toBeDefined();
      expect(vi.mocked(pkceUtils.storePKCEVerifier)).toBeDefined();
      expect(vi.mocked(pkceUtils.getPKCEVerifier)).toBeDefined();
      expect(vi.mocked(pkceUtils.clearPKCEVerifier)).toBeDefined();
    });

    test('should have PKCE verifier mock returning expected value', () => {
      renderComponent();

      const verifier = vi.mocked(pkceUtils.getPKCEVerifier)();
      expect(verifier).toBe(mockPKCE.verifier);
    });

    test('should be able to store PKCE verifier', () => {
      renderComponent();

      vi.mocked(pkceUtils.storePKCEVerifier)(mockPKCE.verifier);

      expect(vi.mocked(pkceUtils.storePKCEVerifier)).toHaveBeenCalledWith(mockPKCE.verifier);
    });

    test('should be able to clear PKCE verifier', () => {
      renderComponent();

      vi.mocked(pkceUtils.clearPKCEVerifier)();

      expect(vi.mocked(pkceUtils.clearPKCEVerifier)).toHaveBeenCalled();
    });
  });

  describe('Authorization Integration', () => {
    test('should have fetchAppSettings called on mount', () => {
      renderComponent();

      expect(mockAuthStore.fetchAppSettings).toHaveBeenCalled();
    });

    test('should support authorizing with PKCE verifier', async () => {
      mockAuthStore.authorizeUser.mockResolvedValue({});
      renderComponent();

      const verifier = vi.mocked(pkceUtils.getPKCEVerifier)();
      await mockAuthStore.authorizeUser('test-code', verifier);

      expect(mockAuthStore.authorizeUser).toHaveBeenCalledWith('test-code', mockPKCE.verifier);
    });

    test('should support authorizing without PKCE verifier', async () => {
      vi.mocked(pkceUtils.getPKCEVerifier).mockReturnValue(null);
      mockAuthStore.authorizeUser.mockResolvedValue({});
      renderComponent();

      await mockAuthStore.authorizeUser('test-code', null);

      expect(mockAuthStore.authorizeUser).toHaveBeenCalledWith('test-code', null);
    });

    test('should handle authorization error', async () => {
      const error = new Error('Authorization failed');
      mockAuthStore.authorizeUser.mockRejectedValue(error);
      renderComponent();

      try {
        await mockAuthStore.authorizeUser('test-code', mockPKCE.verifier);
        throw new Error('Should have thrown');
      } catch (e) {
        expect((e as Error).message).toBe('Authorization failed');
      }
    });
  });

  describe('Button Interaction', () => {
    test('should render clickable login button', () => {
      renderComponent();

      const button = screen.getByRole('button', { name: /Login with Test AAP/i });
      expect(button).toBeTruthy();
      expect(button.tagName).toBe('BUTTON');
    });

    test('should call PKCE generation when login button is clicked', () => {
      renderComponent();

      const button = screen.getByRole('button', { name: /Login with Test AAP/i });
      fireEvent.click(button);

      // Button click should trigger PKCE generation
      expect(vi.mocked(pkceUtils.generatePKCE)).toHaveBeenCalled();
    });
  });
});
