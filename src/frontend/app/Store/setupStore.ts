import { create } from 'zustand';
import api from '@app/client/apiClient';
import {
  ClusterSetupData,
  CostSetupData,
  ConnectionTestResult,
  InfraSetupData,
  SetupMeResponse,
  SetupStatus,
  SyncProgress,
  SyncSetupData,
} from '@app/Types/SetupTypes';

const DEFAULT_CLUSTER: ClusterSetupData = {
  protocol: 'https',
  address: '',
  port: 443,
  aap_version: 'AAP 2.5',
  verify_ssl: true,
  sync_mode: 'api',
  client_id: '',
  client_secret: '',
  access_token: '',
  refresh_token: '',
  db_host: '',
  db_port: 5432,
  db_name: 'awx',
  db_user: '',
  db_password: '',
};

const DEFAULT_SYNC: SyncSetupData = {
  mode: 'days',
  initial_sync_days: 30,
  initial_sync_since: null,
};

const DEFAULT_INFRA: InfraSetupData = {
  dashboard_host: '',
  db_host: '',
  db_username: 'aapdashboard',
  db_password: '',
  db_name: 'aapdashboard',
  db_admin_username: 'postgres',
  db_admin_password: '',
  dashboard_admin_password: '',
  nginx_http_port: 8083,
  nginx_https_port: 8447,
  dashboard_tls_cert: '',
  dashboard_tls_key: '',
};

const DEFAULT_COSTS: CostSetupData = {
  monthly_subscription_cost: 50000,
  engineer_avg_hourly_rate: 50,
};

type SetupStoreState = {
  cluster: ClusterSetupData;
  sync: SyncSetupData;
  infra: InfraSetupData;
  costs: CostSetupData;
  connectionTest: 'idle' | 'testing' | 'success' | 'failed';
  connectionError: string | null;
  configureStatus: 'idle' | 'pending' | 'success' | 'failed';
  configureError: string | null;
  syncProgress: SyncProgress | null;
  localLoginError: string | null;
  setupMe: SetupMeResponse | null;
  setupRequired: boolean | null;
};

type SetupStoreActions = {
  setCluster: (data: Partial<ClusterSetupData>) => void;
  setSync: (data: Partial<SyncSetupData>) => void;
  setInfra: (data: Partial<InfraSetupData>) => void;
  setCosts: (data: Partial<CostSetupData>) => void;
  fetchSetupStatus: () => Promise<boolean>;
  fetchSetupMe: () => Promise<SetupMeResponse>;
  localLogin: (username: string, password: string) => Promise<void>;
  testConnection: () => Promise<ConnectionTestResult>;
  configure: () => Promise<void>;
  pollSyncProgress: () => Promise<SyncProgress>;
  downloadInventory: () => Promise<void>;
};

export const useSetupStore = create<SetupStoreState & SetupStoreActions>((set, get) => ({
  cluster: { ...DEFAULT_CLUSTER },
  sync: { ...DEFAULT_SYNC },
  infra: { ...DEFAULT_INFRA },
  costs: { ...DEFAULT_COSTS },
  connectionTest: 'idle',
  connectionError: null,
  configureStatus: 'idle',
  configureError: null,
  syncProgress: null,
  localLoginError: null,
  setupMe: null,
  setupRequired: null,

  setCluster: (data) => set((s) => ({ cluster: { ...s.cluster, ...data } })),
  setSync: (data) => set((s) => ({ sync: { ...s.sync, ...data } })),
  setInfra: (data) => set((s) => ({ infra: { ...s.infra, ...data } })),
  setCosts: (data) => set((s) => ({ costs: { ...s.costs, ...data } })),

  fetchSetupStatus: async () => {
    const res = await api.get<SetupStatus>('/api/v1/setup/status/');
    set({ setupRequired: res.data.setup_required });
    return res.data.setup_required;
  },

  fetchSetupMe: async () => {
    const res = await api.get<SetupMeResponse>('/api/v1/setup/me/');
    set({ setupMe: res.data });
    return res.data;
  },

  localLogin: async (username, password) => {
    set({ localLoginError: null });
    try {
      await api.post('/api/v1/setup/local_login/', { username, password });
      await get().fetchSetupMe();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error ?? 'Login failed';
      set({ localLoginError: msg });
      throw new Error(msg);
    }
  },

  testConnection: async () => {
    set({ connectionTest: 'testing', connectionError: null });
    const { cluster } = get();
    try {
      const res = await api.post<ConnectionTestResult>('/api/v1/setup/test_connection/', {
        protocol: cluster.protocol,
        address: cluster.address,
        port: cluster.port,
        access_token: cluster.access_token,
        verify_ssl: cluster.verify_ssl,
      });
      const result = res.data;
      set({ connectionTest: result.success ? 'success' : 'failed', connectionError: result.error });
      return result;
    } catch {
      set({ connectionTest: 'failed', connectionError: 'Connection test failed' });
      return { success: false, detected_version: null, error: 'Connection test failed' };
    }
  },

  configure: async () => {
    set({ configureStatus: 'pending', configureError: null });
    const { cluster, sync, costs } = get();
    const clusterPayload: Record<string, unknown> = {
      protocol: cluster.protocol,
      address: cluster.address,
      port: cluster.port,
      aap_version: cluster.aap_version,
      verify_ssl: cluster.verify_ssl,
      sync_mode: cluster.sync_mode,
    };
    if (cluster.sync_mode === 'database') {
      clusterPayload.db_host = cluster.db_host;
      clusterPayload.db_port = cluster.db_port;
      clusterPayload.db_name = cluster.db_name;
      clusterPayload.db_user = cluster.db_user;
      if (cluster.db_password) {
        clusterPayload.db_password = cluster.db_password;
      }
    } else {
      clusterPayload.client_id = cluster.client_id;
      clusterPayload.client_secret = cluster.client_secret;
      clusterPayload.access_token = cluster.access_token;
      clusterPayload.refresh_token = cluster.refresh_token;
    }
    const payload = {
      cluster: clusterPayload,
      sync: {
        initial_sync_days: sync.mode === 'days' ? sync.initial_sync_days : undefined,
        initial_sync_since: sync.mode === 'since' ? sync.initial_sync_since : null,
      },
      costs: {
        monthly_subscription_cost: costs.monthly_subscription_cost,
        engineer_avg_hourly_rate: costs.engineer_avg_hourly_rate,
      },
    };
    try {
      await api.post('/api/v1/setup/configure/', payload);
      set({ configureStatus: 'success' });
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { error?: string } } })?.response?.data?.error ?? 'Configuration failed';
      set({ configureStatus: 'failed', configureError: msg });
      throw new Error(msg);
    }
  },

  pollSyncProgress: async () => {
    const res = await api.get<SyncProgress>('/api/v1/setup/sync_progress/');
    set({ syncProgress: res.data });
    return res.data;
  },

  downloadInventory: async () => {
    const { cluster, sync, infra, costs } = get();
    const inventoryClusterPayload: Record<string, unknown> = {
      protocol: cluster.protocol,
      address: cluster.address,
      port: cluster.port,
      aap_version: cluster.aap_version,
      verify_ssl: cluster.verify_ssl,
      sync_mode: cluster.sync_mode,
    };
    if (cluster.sync_mode === 'database') {
      inventoryClusterPayload.db_host = cluster.db_host;
      inventoryClusterPayload.db_port = cluster.db_port;
      inventoryClusterPayload.db_name = cluster.db_name;
      inventoryClusterPayload.db_user = cluster.db_user;
      if (cluster.db_password) {
        inventoryClusterPayload.db_password = cluster.db_password;
      }
    } else {
      inventoryClusterPayload.client_id = cluster.client_id;
      inventoryClusterPayload.client_secret = cluster.client_secret;
      inventoryClusterPayload.access_token = cluster.access_token;
      inventoryClusterPayload.refresh_token = cluster.refresh_token;
    }
    const payload = {
      cluster: inventoryClusterPayload,
      sync: {
        initial_sync_days: sync.mode === 'days' ? sync.initial_sync_days : undefined,
        initial_sync_since: sync.mode === 'since' ? sync.initial_sync_since : null,
      },
      costs: {
        monthly_subscription_cost: costs.monthly_subscription_cost,
        engineer_avg_hourly_rate: costs.engineer_avg_hourly_rate,
      },
      infra: { ...infra },
    };
    const res = await api.post('/api/v1/setup/inventory/', payload, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data as BlobPart], { type: 'text/plain' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'inventory');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },
}));

export default useSetupStore;
