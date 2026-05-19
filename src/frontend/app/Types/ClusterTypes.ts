export type AAPVersion = 'AAP 2.4' | 'AAP 2.5' | 'AAP 2.6' | 'AAP 2.7';

export interface ClusterInfo {
  id: number;
  protocol: 'http' | 'https';
  address: string;
  port: number;
  aap_version: AAPVersion;
  verify_ssl: boolean;
  sync_mode: 'api' | 'database';
  client_id: string;
  has_access_token: boolean;
  has_refresh_token: boolean;
  db_host: string;
  db_port: number;
  db_name: string;
  db_user: string;
  has_db_password: boolean;
  last_synced: string | null;
}

export interface ClusterFormData {
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

export interface ConnectionTestResult {
  success: boolean;
  detected_version: string | null;
  error: string | null;
}
