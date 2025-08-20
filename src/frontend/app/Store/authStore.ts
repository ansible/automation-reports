import { create } from 'zustand';
import { RestService } from '@app/Services';
import { AppSettings, AuthResponse, MyUserData } from '@app/Types/AuthTypes';

type AuthStoreState = {
  appSettings: AppSettings | null;
  myUserData: MyUserData | null;
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: boolean;
  logErrorMessage?: string | null;
}

type AuthStoreActions = {
  fetchAppSettings: () => Promise<void>;
  authorizeUser: (authCode: string) => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  getMyUserData: () => Promise<void>;
  logout: () => Promise<void>;
  logError: (message: string) => void;
}

type AuthStoreSelectors = {
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthStoreState & AuthStoreActions & AuthStoreSelectors>((set, get) => ({
  appSettings: null,
  myUserData: null,
  loading: 'idle',
  error: false,
  logErrorMessage: null,

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
      await RestService.authorizeUser(authCode, callback_uri);
      set({
        loading: 'succeeded'
      });
      await get().getMyUserData();
    } catch {
      set({ loading: 'failed', error: true });
      return Promise.reject({ message: 'Failed authorization' });
    }
  },
  refreshAccessToken: async () => {
    try {
      await RestService.refreshAccessToken();
      set({
        loading: 'succeeded'
      });
      return Promise.resolve();
    } catch (error) {
      set({ loading: 'failed', error: false });
      return Promise.reject(error);
    }
  },
  logout: async () => {
    set({ myUserData: null });
    await RestService.logoutUser();
    return Promise.resolve();
  },
  getMyUserData: async () => {
    const { myUserData } = get();
    if (myUserData?.id) {
      return;
    }
    set({ loading: 'pending', error: false });
    try {
      const response = await RestService.getMyUserData();
      set({ myUserData: response, loading: 'succeeded' });
    } catch (error) {
      set({ myUserData: null, loading: 'succeeded' });
      return Promise.reject(error);
    }
  },
  isAuthenticated: () => !!get().myUserData,
  logError: (message: string) => {
    set({ logErrorMessage: message });
  },
}));


export default useAuthStore;
