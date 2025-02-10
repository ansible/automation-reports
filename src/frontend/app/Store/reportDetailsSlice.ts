import { RestService } from "@app/Services";
import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { RootState } from "./store";
import { ReportDetailsResponse, ReportDetailsState, TotalOption, User } from "@app/Types/ReportDetailsType";

export const fetchReportDetails = createAsyncThunk(
  'report/details',
  async (params: any): Promise<any> => {
    const queryString = buildQueryString(params);
    const response = await RestService.fetchReportDetails(queryString);
    return response.data;
  }
);

const buildQueryString = (params: any): string => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  });
  return query.toString() ? `?${query.toString()}` : '';
}

const initialState: ReportDetailsState = {
  users: [],
  projects: [],
  totalNumberOfUniqueHosts: null,
  totalNumberOfSuccessfulJobs: null,
  totalNumberOfFailedJobs: null,
  totalNumberOfJobRuns: null,
  totalNumberOfHostJobRuns: null,
  totalHoursOfAutomation: null,
  costOfAutomatedExecution: null,
  costOfManualAutomation: null,
  totalSavings: null,
  jobChart: null,
  hostChart: null,
  loading: 'idle',
  error: null
}

export const reportDetailsSlice = createSlice({
  name: 'reportDetails',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchReportDetails.pending, (state) => {
        state.loading = 'pending';
      })
      .addCase(fetchReportDetails.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        const payload = action.payload as ReportDetailsResponse;
        state.users = payload.users;
        state.projects = payload.projects;
        state.totalNumberOfUniqueHosts = payload.total_number_of_unique_hosts;
        state.totalNumberOfSuccessfulJobs = payload.total_number_of_successful_jobs;
        state.totalNumberOfFailedJobs = payload.total_number_of_failed_jobs;
        state.totalNumberOfJobRuns = payload.total_number_of_job_runs;
        state.totalNumberOfHostJobRuns = payload.total_number_of_host_job_runs;
        state.totalHoursOfAutomation = payload.total_hours_of_automation;
        state.costOfAutomatedExecution = payload.cost_of_automated_execution;
        state.costOfManualAutomation = payload.cost_of_manual_automation;
        state.totalSavings = payload.total_saving;
        state.jobChart = payload.job_chart;
        state.hostChart = payload.host_chart;
      })
      .addCase(fetchReportDetails.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.error.message;
      });
  },
});

export default reportDetailsSlice.reducer;

export const reportUsers = (state: RootState) => state.reportDetails.users;
export const reportProjects = (state: RootState) => state.reportDetails.projects;
export const totalNumberOfUniqueHosts = (state: RootState) => state.reportDetails.totalNumberOfUniqueHosts;
export const totalNumberOfSuccessfulJobs = (state: RootState) => state.reportDetails.totalNumberOfSuccessfulJobs;
export const totalNumberOfFailedJobs = (state: RootState) => state.reportDetails.totalNumberOfFailedJobs;
export const totalNumberOfJobRuns = (state: RootState) => state.reportDetails.totalNumberOfJobRuns;
export const totalNumberOfHostJobRuns = (state: RootState) => state.reportDetails.totalNumberOfHostJobRuns;
export const totalHoursOfAutomation = (state: RootState) => state.reportDetails.totalHoursOfAutomation;
export const costOfAutomatedExecution = (state: RootState) => state.reportDetails.costOfAutomatedExecution;
export const costOfManualAutomation = (state: RootState) => state.reportDetails.costOfManualAutomation;
export const totalSavings = (state: RootState) => state.reportDetails.totalSavings;
export const jobChartData = (state: RootState) => state.reportDetails.jobChart;
export const hostChartData = (state: RootState) => state.reportDetails.hostChart;
