export interface ReportDetailsResponse {
  users: User[];
  projects: Project[];
  total_number_of_unique_hosts: TotalOption;
  total_number_of_successful_jobs: TotalOption;
  total_number_of_failed_jobs: TotalOption;
  total_number_of_job_runs: TotalOption;
  total_number_of_host_job_runs: TotalOption;
  total_hours_of_automation: TotalOption;
  cost_of_automated_execution: TotalOption;
  cost_of_manual_automation: TotalOption;
  total_saving: TotalOption;
  job_chart: ChartDataType;
  host_chart: ChartDataType;
}

export interface User {
  user_id: number | string;
  user_name: string | null;
  count: number;
}

export interface Project {
  project_id: number | string;
  project_name: string | null;
  count: number;

}

export interface TotalOption {
  value: number;
  index: number;
}

export interface ChartItem {
  x: Date | string;
  y: number;
}

export interface ChartDataType {
  items: ChartItem[],
  range: string | null,
}

export interface ReportDetailsState {
  users: User[],
  projects: Project[],
  totalNumberOfUniqueHosts: TotalOption | null,
  totalNumberOfSuccessfulJobs: TotalOption | null,
  totalNumberOfFailedJobs: TotalOption | null,
  totalNumberOfJobRuns: TotalOption | null,
  totalNumberOfHostJobRuns: TotalOption | null,
  totalHoursOfAutomation: TotalOption | null,
  costOfAutomatedExecution: TotalOption | null,
  costOfManualAutomation: TotalOption | null,
  totalSavings: TotalOption | null,
  jobChart: ChartDataType | null,
  hostChart: ChartDataType | null,
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: string | null | undefined;
}