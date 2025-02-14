export type paginationProps = {
  onPageChange: (newPage: number) => void;
  onPerPageChange: (page: number, newPage: number) => void;
  totalItems: number;
};

export type SortProps = {
  onSortChange: (ordering: string) => void;
};

export type columnProps = {
  name: string;
  title: string;
  valueKey?: string;
  type?: 'currency' | 'string' | 'number';
  info?: {
    tooltip?: string;
  };
  isEditable?: boolean;
};

export type UrlParams = {
  page?: number;
  page_size?: number;
  organization?: number[] | null;
  date_range?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  label?: number[] | null;
  job_template?: number[] | null;
  ordering?: string | null;
};

export type TableResult = {
  name: string;
  runs: number;
  elapsed: number;
  cluster: number;
  elapsed_str: string;
  num_hosts: number;
  manual_time: number;
  successful_runs: number;
  failed_runs: number;
  automated_costs: number;
  manual_costs: number;
  savings: number;
  job_template_id: number;
};

export type TableResponse = {
  count: number;
  results: TableResult[];
};

export type ValueIndex = {
  value: number;
  index: number;
};

export type DashboardTableProps = {
  onCostChanged: (type: string, value: number) => void;
  onItemEdit: (value: number, item: TableResult) => void;
  data: TableResponse;
  totalSaving: ValueIndex;
  costOfManualAutomation: ValueIndex;
  costOfAutomatedExecution: ValueIndex;
  loading: boolean;
};

export type TopUser = {
  user_id: number;
  user_name: string;
  count: string;
};

export type TopProject = {
  project_id: number;
  project_name: string;
  count: string;
};

export type ChartRange = 'hour' | 'day' | 'month' | 'year';

export type ChartData = {
  items: { x: Date | string; y: number }[];
  range: ChartRange;
};

export type ReportDetail = {
  users: TopUser[];
  projects: TopProject[];
  total_number_of_unique_hosts: ValueIndex;
  total_number_of_successful_jobs: ValueIndex;
  total_number_of_failed_jobs: ValueIndex;
  total_number_of_job_runs: ValueIndex;
  total_number_of_host_job_runs: ValueIndex;
  total_hours_of_automation: ValueIndex;
  cost_of_automated_execution: ValueIndex;
  cost_of_manual_automation: ValueIndex;
  total_saving: ValueIndex;
  job_chart: ChartData;
  host_chart: ChartData;
};

export type DashboardTopTableColumn = {
  name: string;
  title: string;
};

export type DashboardTopTableProps = {
  title: string;
  columns: DashboardTopTableColumn[];
  data: TopUser[] | TopProject[];
};
