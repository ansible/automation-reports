import api from "./apiClient";
import { useAuthStore } from '@app/Store/authStore';
import { AxiosResponse, AxiosError } from "axios";

api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalConfig = error.config;
    const { refreshAccessToken, logout, logError } = useAuthStore.getState();
    if (!originalConfig) {
      return Promise.reject(error);
    }

    if (error?.response?.status === 403) {
      logError("You don't have permissions to view this content.");
      return Promise.reject(error);
    }

    if (error?.response?.status === 401) {
      if (originalConfig.url === "/api/v1/aap_auth/refresh_token/" || originalConfig.url === "/api/v1/aap_auth/token/") {
        //logout();
        return Promise.reject(error);
      } else {
        try {
          await refreshAccessToken();
        } catch (error) {
          //logout();
          return Promise.reject(error);
        }
        return api(originalConfig);
      }
    } else {
      return Promise.reject(error);
    }
  }
);

