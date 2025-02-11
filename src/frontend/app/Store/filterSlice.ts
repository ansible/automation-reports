import { createAsyncThunk, createSelector, createSlice } from '@reduxjs/toolkit';
import { RootState } from '@app/Store/store';
import { RestService } from '@app/Services';
import { FilterOption, FilterOptionResponse, FilterOptionWithId, FilterState } from '@app/Types';
import { listToDict } from '@app/Utils';

export const fetchTemplateOptions = createAsyncThunk('filters/options', async (): Promise<FilterOptionResponse> => {
  const response = await RestService.fetchTemplateOptions();
  return response.data;
});

const initialState: FilterState = {
  filterOptions: [
    { key: 'job_template', value: 'Template' },
    { key: 'organization', value: 'Organization' },
    { key: 'label', value: 'Labels' },
  ],
  automatedProcessCost: 0,
  clusters: [],
  dateRangeOptions: [],
  templateOptions: [],
  labelOptions: [],
  manualCostAutomation: 0,
  organizationOptions: [],
  instanceOptions: [],
  loading: 'idle',
  error: null,
};

export const filterSlice = createSlice({
  name: 'filter',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchTemplateOptions.pending, (state) => {
        state.loading = 'pending';
      })
      .addCase(fetchTemplateOptions.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        const payload = action.payload as FilterOptionResponse;
        state.instanceOptions = payload.instances;
        state.labelOptions = payload.labels;
        state.templateOptions = payload.job_templates;
        state.organizationOptions = payload.organizations;
        state.dateRangeOptions = payload.date_ranges;
        state.manualCostAutomation = payload.manual_cost_automation;
        state.automatedProcessCost = payload.automated_process_cost;
      })
      .addCase(fetchTemplateOptions.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.error.message;
      });
  },
});

export default filterSlice.reducer;

export const filterOptions = (state: RootState) => state.filters.filterOptions;
export const instanceOptions = (state: RootState) => state.filters.instanceOptions;
export const templateOptions = (state: RootState) => state.filters.templateOptions;
export const organizationOptions = (state: RootState) => state.filters.organizationOptions;
export const labelOptions = (state: RootState) => state.filters.labelOptions;
export const dateRangeOptions = (state: RootState) => state.filters.dateRangeOptions;
export const manualCostAutomation = (state: RootState) => state.filters.manualCostAutomation;
export const automatedProcessCost = (state: RootState) => state.filters.automatedProcessCost;

export const filterChoicesData = createSelector(
  [instanceOptions, templateOptions, organizationOptions, labelOptions],
  (
    instanceOptions: FilterOptionWithId[],
    templateOptions: FilterOptionWithId[],
    organizationOptions: FilterOption[],
    labelOptions: FilterOptionWithId[],
  ) => {
    return {
      instances: instanceOptions,
      job_template: templateOptions,
      organization: organizationOptions,
      label: labelOptions,
    };
  },
);

export const filterOptionsById = createSelector([filterOptions], (filterOptions) => listToDict(filterOptions));

export const filterChoicesDataById = createSelector([filterChoicesData], (filterChoicesData) => {
  return {
    instances: listToDict(filterChoicesData.instances),
    job_template: listToDict(filterChoicesData.job_template),
    organization: listToDict(filterChoicesData.organization),
    label: listToDict(filterChoicesData.label),
  };
});
