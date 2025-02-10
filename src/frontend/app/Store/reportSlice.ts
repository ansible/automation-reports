import { RestService } from '@app/Services';
import { Report, ReportState, ReportResponse } from '@app/Types';
import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { RootState } from './store';

export const fetchReports = createAsyncThunk(
  'reports',
  async (params: any): Promise<ReportResponse> => {
    const queryString = buildQueryString(params);
    const response = await RestService.fetchReports(queryString);
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

const initialState: ReportState = {
  reports: [] as Report[],
  count: 0,
  loading: 'idle',
  error: null
}

export const reportSlice = createSlice({
  name: 'report',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchReports.pending, (state) => {
        state.loading = 'pending';
      })
      .addCase(fetchReports.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        const payload = action.payload as ReportResponse;
        state.reports = payload.results;    
        state.count = payload.count;    
      })
      .addCase(fetchReports.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.error.message;
      });
  },
});

export default reportSlice.reducer;

export const reportResults = (state: RootState) => state.reports;
export const reportsLoading = (state: RootState) => state.reports.loading;


