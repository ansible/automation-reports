import { ChartData } from '@app/Types/TableTypes';

export interface Report {
  name: string;
  runs: number;
  elapsed: string;
  cluster: number;
  elapsed_str: string;
  num_hosts: number;
  time_taken_manually_execute_minutes: number;
  time_taken_create_automation_minutes: number;
  successful_runs: number;
  failed_runs: number;
  automated_costs: string;
  manual_costs: string;
  savings: string;
}

export interface ReportResponse {
  count: number;
  next: string;
  previous: string;
  results: Report[];
}

export interface ReportState {
  reports: Report[];
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: string | null | undefined;
  count: number;
}

export type DashboardChartProps = {
  value: number;
  index: number;
  chartData: ChartData;
  loading: boolean;
};
