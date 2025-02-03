export interface FilterOption {
  key: string | number;
  value: string;
}

export interface FilterOptionResponse {
  organizations: FilterOption[];
  instances: FilterOption[];
  templates: FilterOption[];
  date_ranges: FilterOption[];
}

export interface FilterState {
  filterOptions: FilterOption[];
  instanceOptions: FilterOption[];
  templateOptions: FilterOption[];
  organizationOptions: FilterOption[];
  dateRangeOptions: FilterOption[];
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: string | null | undefined;
}
