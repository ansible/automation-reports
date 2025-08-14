import api from "./apiClient";
import { useAuthStore } from '@app/Store/authStore';
import { AxiosResponse, AxiosError } from "axios";


api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token && config.headers && config.url !== "/api/v1/aap_auth/refresh_token/") {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error: AxiosError) => {
    console.error("Request error", error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalConfig = error.config;
    const { refreshAccessToken, logout } = useAuthStore.getState();
    if (!originalConfig) {
      return Promise.reject(error);
    }

    if (error?.response?.status === 401) {
      if (originalConfig.url === "/api/v1/aap_auth/refresh_token/") {
        console.log("LOGOUT");
        logout();
        return Promise.reject(error);
      } else {
        try {
          await refreshAccessToken();
        } catch (error) {
          logout();
          return Promise.reject(error);
        }
        return api(originalConfig);
      }
    } else {
      return Promise.reject(error);
    }
  }
);

  