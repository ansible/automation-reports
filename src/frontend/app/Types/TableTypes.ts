import { PaginationParams } from '@app/Types/FilterTypes';
import React from 'react';

export type PaginationProps = {
  onPageChange: (newPage: number) => void;
  onPerPageChange: (page: number, newPage: number) => void;
  currentPage: number;
  perPage: number;
  totalItems: number;
};

export type SortProps = {
  onSortChange: (ordering: string) => void;
};

export type ColumnProps = {
  name: string;
  title: string;
  valueKey?: string;
  type?: 'currency' | 'string' | 'number' | 'time-string';
  info?: {
    tooltip?: string;
  };
  isEditable?: boolean;
  isVisible: boolean;
};

export type TableResult = {
  name: string;
  runs: number;
  elapsed: number;
  cluster: number;
  elapsed_str: string;
  num_hosts: number;
  time_taken_manually_execute_minutes: number;
  time_taken_create_automation_minutes: number;
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
  value: number | string;
};

export type DashboardTableProps = {
  onCostChanged: (type: string, value: number) => void;
  onItemEdit: (newValue: TableResult, oldValue: TableResult) => void;
  onInputFocus: (event?: never) => void;
  onPaginationChange: (pagination: PaginationParams) => void;
  onSortChange: (ordering: string) => void;
  onExportCsv: () => void;
  onEnableTemplateCreationTimeChange: (checked: boolean) => void;
  pagination: PaginationParams;
  data: TableResponse;
  totalSaving: ValueIndex;
  costOfManualAutomation: ValueIndex;
  costOfAutomatedExecution: ValueIndex;
  totalTimeSavings: ValueIndex;
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

export type ReportDetailLinks = {
  successful_jobs?: string;
  failed_jobs?: string;
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
  total_time_saving: ValueIndex;
  related_links?: ReportDetailLinks;
};

export type DashboardTopTableProps = {
  title: string;
  columns: ColumnProps[];
  data: TopUser[] | TopProject[];
  tooltip?: string | React.ReactNode
  infoIcon?: boolean
};
