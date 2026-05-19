export type AAPVersion = 'AAP 2.4' | 'AAP 2.5' | 'AAP 2.6' | 'AAP 2.7';

export interface ClusterSetupData {
  protocol: 'http' | 'https';
  address: string;
  port: number;
  aap_version: AAPVersion;
  verify_ssl: boolean;
  sync_mode: 'api' | 'database';
  client_id: string;
  client_secret: string;
  access_token: string;
  refresh_token: string;
  db_host: string;
  db_port: number;
  db_name: string;
  db_user: string;
  db_password: string;
}

export type SyncMode = 'days' | 'since';

export interface SyncSetupData {
  mode: SyncMode;
  initial_sync_days: number;
  initial_sync_since: string | null;
}

export interface InfraSetupData {
  dashboard_host: string;
  db_host: string;
  db_username: string;
  db_password: string;
  db_name: string;
  db_admin_username: string;
  db_admin_password: string;
  dashboard_admin_password: string;
  nginx_http_port: number;
  nginx_https_port: number;
  dashboard_tls_cert: string;
  dashboard_tls_key: string;
}

export interface CostSetupData {
  monthly_subscription_cost: number;
  engineer_avg_hourly_rate: number;
}

export interface SetupStatus {
  setup_required: boolean;
}

export interface SetupMeResponse {
  authenticated: boolean;
  is_superuser: boolean;
  username: string | null;
}

export interface ConnectionTestResult {
  success: boolean;
  detected_version: string | null;
  error: string | null;
}

export interface SyncProgress {
  has_synced: boolean;
  last_synced: string | null;
  cluster_configured: boolean;
}
