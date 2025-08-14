import { create } from 'zustand';
import { RestService } from '@app/Services';
import { AppSettings, AuthResponse, MyUserData } from '@app/Types/AuthTypes';

const REDIRECT_URLS = {
  dashboard: '/',
  login: '/login',
};

type AuthStoreState = {
  appSettings: AppSettings | null;
  myUserData: MyUserData | null;
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: boolean;
  accessToken?: string | null;
  refreshToken?: string | null;
}

type AuthStoreActions = {
  fetchAppSettings: () => Promise<void>;
  authorizeUser: (authCode: string) => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  getMyUserData: () => Promise<void>;
  logout: () => void;
}

type AuthStoreSelectors = {
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthStoreState & AuthStoreActions & AuthStoreSelectors>((set, get) => ({
  appSettings: null,
  myUserData: null,
  loading: 'idle',
  error: false,
  accessToken: localStorage.getItem('jwtAccessToken') || null,
  refreshToken: localStorage.getItem('jwtRefreshToken') || null,

  fetchAppSettings: async () => {
    set({ loading: 'pending', error: false });
    try {
      const response = await RestService.fetchAapSettings();
      const appSettings: AppSettings = response.data;
      set({ appSettings, loading: 'succeeded' });
    } catch {
      set({ loading: 'failed', error: true });
    }
  },
  authorizeUser: async (authCode: string) => {
    if (!authCode) {
      console.error('Authorization code is required');
      return;
    }
    const callback_uri = window.location.origin + '/auth-callback';
    set({ loading: 'pending', error: false });
    try {
      const response = await RestService.authorizeUser(authCode, callback_uri);
      const { access_token, refresh_token } = response;
      localStorage.setItem('jwtAccessToken', access_token);
      localStorage.setItem('jwtRefreshToken', refresh_token);
      set({
        accessToken: access_token,
        refreshToken: refresh_token,
        loading: 'succeeded',
      });
      await get().getMyUserData();
      window.location.href = REDIRECT_URLS.dashboard;
    } catch {
      set({ loading: 'failed', error: true });
      return Promise.reject({ message: 'Failed authorization' });
    }
  },
  refreshAccessToken: async () => {
    const { accessToken, refreshToken, logout } = get();
    if (!accessToken || !refreshToken) {
      logout();
      set({ loading: 'failed', error: true });
      return Promise.reject({ message: 'Unauthorized' });
    }

    try {
      const response: AuthResponse = await RestService.refreshAccessToken(accessToken, refreshToken);
      const { access_token, refresh_token } = response;
      set({
        accessToken: access_token,
        refreshToken: refresh_token,
        loading: 'succeeded',
      })
      localStorage.setItem('jwtAccessToken', access_token);
      localStorage.setItem('jwtRefreshToken', refresh_token);
      return Promise.resolve();
    } catch (error) {
      set({ loading: 'failed', error: true });
      return Promise.reject({ message: 'Unauthorized' });
    }
  },
  logout:  async () => {
    localStorage.removeItem('jwtAccessToken');
    localStorage.removeItem('jwtRefreshToken');
    set({ accessToken: null, refreshToken: null });
    window.location.href = REDIRECT_URLS.login;
  },
  getMyUserData: async () => {
    const { logout, myUserData } = get();
    if (myUserData?.id) {
      return;
    }
    set({ loading: 'pending', error: false });
    try {
      const response = await RestService.getMyUserData();
      set({ myUserData: response, loading: 'succeeded' });
    } catch (error) {
      logout();
      set({ loading: 'failed', error: true });
      return Promise.reject(error);
    }
  },
  isAuthenticated: () => !!get().accessToken,
}));


export default useAuthStore;