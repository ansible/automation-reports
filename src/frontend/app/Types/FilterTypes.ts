export interface FilterOption {
  key: string | number;
  value: string;
}

export interface ClusterOption {
  key: string | number;
  address: string;
}

export interface FilterOptionWithId {
  key: string | number;
  value: string;
  cluster_id: string | number;
}

export interface Currency {
  id: number;
  name: string;
  iso_code: string;
  symbol: string;
}

export interface FilterOptionResponse {
  automated_process_cost: number | string;
  clusters: ClusterOption[];
  date_ranges: FilterOption[];
  labels: FilterOptionWithId[];
  manual_cost_automation: number | string;
  organizations: FilterOption[];
  instances: FilterOptionWithId[];
  currencies: Currency[];
  projects: FilterOptionWithId[];
  currency: number;
  enable_template_creation_time: boolean;
  filter_sets: FilterSet[];
  max_pdf_job_templates: number,
}

export interface Settings {
  type: string;
  value: number;
}

export interface FilterState {
  filterOptions: FilterOption[];
  automatedProcessCost: number | string;
  clusters: ClusterOption[];
  dateRangeOptions: FilterOption[];
  //templateOptions: FilterOptionWithId[];
  //labelOptions: FilterOptionWithId[];
  //instanceOptions: FilterOptionWithId[];
  //projectOptions: FilterOptionWithId[];
  manualCostAutomation: number | string;
  //organizationOptions: FilterOption[];
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: boolean;
  max_pdf_job_templates: number,
}


export interface FilterOptionsState {
  endPoint: string;
  options: FilterOption[];
  currentPage: number,
  pageSize: number,
  count: number,
  nextPage: string | null,
  prevPage: string | null,
  searchString: string | null,
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: boolean;
}


export interface RequestFilter {
  organization?: (string | number)[];
  job_template?: (string | number)[];
  label?: (string | number)[];
  project?: (string | number)[];
  date_range: string;
  start_date?: string;
  end_date?: string;
}

export interface FilterSet {
  id?: number;
  name: string;
  filters: RequestFilter;
}

export interface CommonState {
  currencyOptions: Currency[];
  filterSetOptions: FilterSet[];
  selectedCurrency: number | undefined;
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: boolean;
  viewSavingProcess: boolean;
  viewSaveError: string | null;
  selectedView: number | null | undefined;
  enableTemplateCreationTime: boolean;
}

export interface FilterProps {
  organization: FilterOptionWithId[];
  job_template: FilterOptionWithId[];
  label: FilterOptionWithId[];
  project: FilterOptionWithId[];
  date_range: string | null;
  start_date: Date | undefined;
  end_date: Date | undefined;
}

export interface FilterComponentProps {
  onChange: (requestFilter: RequestFilter) => void;
}

export interface AddEditViewProps {
  filters: FilterProps;
  onViewDelete: () => void;
}

export type PaginationParams = {
  page: number;
  page_size: number;
};

export type OrderingParams = {
  ordering?: string;
};

export type UrlParams = RequestFilter & PaginationParams & OrderingParams;

export type OptionsResponse = {
  count: number,
  next: string | null,
  previous: string | null,
  results: FilterOptionWithId[]
}
