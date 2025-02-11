export interface FilterOption {
  key: string | number;
  value: string;
}

export interface ClusterOption {
  key: string | number;
  address: string;
}

export interface FilterOptionWithId {
  ket: string | number;
  value: string;
  cluster_id: string | number;
}

export interface FilterOptionResponse {
  automated_process_cost: number | string;
  clusters: ClusterOption[];
  date_ranges: FilterOption[];
  job_templates: FilterOptionWithId[];
  labels: FilterOptionWithId[];
  manual_cost_automation: number | string;
  organizations: FilterOption[];
  instances: FilterOptionWithId[];
}

export interface FilterState {
  filterOptions: FilterOption[];
  automatedProcessCost: number | string;
  clusters: ClusterOption[];
  dateRangeOptions: FilterOption[];
  templateOptions: FilterOptionWithId[];
  labelOptions: FilterOptionWithId[];
  instanceOptions: FilterOptionWithId[];
  manualCostAutomation: number | string;
  organizationOptions: FilterOption[];
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: string | null | undefined;
}
