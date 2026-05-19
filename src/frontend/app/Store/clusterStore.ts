import { create } from 'zustand';
import api from '@app/client/apiClient';
import { ClusterInfo, ClusterFormData, ConnectionTestResult } from '@app/Types/ClusterTypes';

type ClusterStoreState = {
  clusters: ClusterInfo[];
  loading: boolean;
  saving: boolean;
  isModalOpen: boolean;
  formMode: 'list' | 'add' | 'edit';
  editingCluster: ClusterInfo | null;
  syncing: number[];
  connectionTest: 'idle' | 'testing' | 'success' | 'failed';
  connectionError: string | null;
  error: string | null;
};

type ClusterStoreActions = {
  fetchClusters: () => Promise<void>;
  openModal: () => void;
  closeModal: () => void;
  startAdd: () => void;
  startEdit: (cluster: ClusterInfo) => void;
  backToList: () => void;
  saveCluster: (data: ClusterFormData) => Promise<void>;
  deleteCluster: (id: number) => Promise<void>;
  syncCluster: (id: number) => Promise<void>;
  testConnection: (
    data: Pick<ClusterFormData, 'protocol' | 'address' | 'port' | 'access_token' | 'verify_ssl'>
  ) => Promise<ConnectionTestResult>;
  testDbConnection: (
    data: Pick<ClusterFormData, 'db_host' | 'db_port' | 'db_name' | 'db_user' | 'db_password'>
  ) => Promise<ConnectionTestResult>;
};

const useClusterStore = create<ClusterStoreState & ClusterStoreActions>((set, get) => ({
  clusters: [],
  loading: false,
  saving: false,
  isModalOpen: false,
  formMode: 'list',
  editingCluster: null,
  syncing: [],
  connectionTest: 'idle',
  connectionError: null,
  error: null,

  fetchClusters: async () => {
    set({ loading: true, error: null });
    try {
      const res = await api.get<ClusterInfo[]>('/api/v1/clusters/');
      set({ clusters: res.data, loading: false });
    } catch {
      set({ loading: false, error: 'Failed to load clusters' });
    }
  },

  openModal: () => {
    set({ isModalOpen: true, formMode: 'list' });
    get().fetchClusters();
  },

  closeModal: () => {
    set({
      isModalOpen: false,
      formMode: 'list',
      editingCluster: null,
      connectionTest: 'idle',
      connectionError: null,
      error: null,
    });
  },

  startAdd: () => {
    set({ formMode: 'add', editingCluster: null, connectionTest: 'idle', connectionError: null });
  },

  startEdit: (cluster: ClusterInfo) => {
    set({ formMode: 'edit', editingCluster: cluster, connectionTest: 'idle', connectionError: null });
  },

  backToList: () => {
    set({ formMode: 'list', editingCluster: null, connectionTest: 'idle', connectionError: null });
  },

  saveCluster: async (data: ClusterFormData) => {
    set({ saving: true, error: null });
    const { formMode, editingCluster } = get();
    try {
      const payload: Record<string, unknown> = {
        protocol: data.protocol,
        address: data.address,
        port: data.port,
        aap_version: data.aap_version,
        verify_ssl: data.verify_ssl,
        sync_mode: data.sync_mode,
      };
      if (data.sync_mode === 'database') {
        payload.db_host = data.db_host;
        payload.db_port = data.db_port;
        payload.db_name = data.db_name;
        payload.db_user = data.db_user;
        if (data.db_password) {
          payload.db_password = data.db_password;
        }
      } else {
        payload.client_id = data.client_id;
        payload.client_secret = data.client_secret || undefined;
        payload.access_token = data.access_token || undefined;
        payload.refresh_token = data.refresh_token || undefined;
      }
      if (formMode === 'edit' && editingCluster) {
        await api.patch(`/api/v1/clusters/${editingCluster.id}/`, payload);
      } else {
        await api.post('/api/v1/clusters/', payload);
      }
      set({ saving: false });
      await get().fetchClusters();
      get().backToList();
    } catch {
      set({ saving: false, error: 'Failed to save cluster' });
      throw new Error('Failed to save cluster');
    }
  },

  deleteCluster: async (id: number) => {
    set({ error: null });
    try {
      await api.delete(`/api/v1/clusters/${id}/`);
      await get().fetchClusters();
    } catch {
      set({ error: 'Failed to delete cluster' });
      throw new Error('Failed to delete cluster');
    }
  },

  syncCluster: async (id: number) => {
    set((s) => ({ syncing: [...s.syncing, id] }));
    try {
      await api.post(`/api/v1/clusters/${id}/sync/`);
    } catch {
      // sync errors are non-fatal; the backend will update status separately
    } finally {
      setTimeout(() => {
        set((s) => ({ syncing: s.syncing.filter((sid) => sid !== id) }));
      }, 3000);
    }
  },

  testConnection: async (
    data: Pick<ClusterFormData, 'protocol' | 'address' | 'port' | 'access_token' | 'verify_ssl'>
  ): Promise<ConnectionTestResult> => {
    set({ connectionTest: 'testing', connectionError: null });
    try {
      const res = await api.post<ConnectionTestResult>('/api/v1/clusters/test_connection/', data);
      const result = res.data;
      set({ connectionTest: result.success ? 'success' : 'failed', connectionError: result.error });
      return result;
    } catch {
      const fallback: ConnectionTestResult = { success: false, detected_version: null, error: 'Connection test failed' };
      set({ connectionTest: 'failed', connectionError: fallback.error });
      return fallback;
    }
  },

  testDbConnection: async (
    data: Pick<ClusterFormData, 'db_host' | 'db_port' | 'db_name' | 'db_user' | 'db_password'>
  ): Promise<ConnectionTestResult> => {
    set({ connectionTest: 'testing', connectionError: null });
    try {
      const res = await api.post<ConnectionTestResult>('/api/v1/clusters/test_connection/', {
        sync_mode: 'database',
        ...data,
      });
      const result = res.data;
      set({ connectionTest: result.success ? 'success' : 'failed', connectionError: result.error });
      return result;
    } catch {
      const fallback: ConnectionTestResult = { success: false, detected_version: null, error: 'Connection test failed' };
      set({ connectionTest: 'failed', connectionError: fallback.error });
      return fallback;
    }
  },
}));

export default useClusterStore;
