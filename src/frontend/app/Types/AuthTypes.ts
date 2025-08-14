export interface AppSettings {
  name: string;
  url: string;
  client_id: string;
  scope: string;
  approval_prompt: string;
  response_type: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
};

export interface MyUserData {
  id: number,
  first_name: string,
  last_name: string,
  email: string,
  is_superuser: boolean,
  is_platform_auditor: boolean
}