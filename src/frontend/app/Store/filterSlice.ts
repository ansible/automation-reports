import { createAsyncThunk, createSelector, createSlice } from '@reduxjs/toolkit';
import { RootState } from '@app/Store/store';
import { RestService } from '@app/Services';
import { FilterOption, FilterOptionResponse, FilterOptionWithId, FilterState } from '@app/Types';
import { listToDict } from '@app/Utils';
import { setCurrencies, setDefaultCurrency, setFilterViews } from '@app/Store/commonSlice';

export const fetchTemplateOptions = createAsyncThunk(
  'filters/options',
  async (_, api): Promise<FilterOptionResponse> => {
    const response = await RestService.fetchTemplateOptions();
    const data = response.data as FilterOptionResponse;
    if (data?.currencies) {
      api.dispatch(setCurrencies(data.currencies));
    }
    if (data?.currency) {
      api.dispatch(setDefaultCurrency(data.currency));
    }
    if (data?.filter_sets) {
      api.dispatch(setFilterViews(data.filter_sets));
    }
    return data;
  },
);

export const setAutomatedProcessCost = createAsyncThunk(
  'filters/automatedProcessCost',
  async (cost: number): Promise<number> => {
    return cost;
  },
);

export const setManualProcessCost = createAsyncThunk(
  'filters/manualProcessCost',
  async (cost: number): Promise<number> => {
    return cost;
  },
);

const initialState: FilterState = {
  filterOptions: [
    { key: 'job_template', value: 'Template' },
    { key: 'organization', value: 'Organization' },
    { key: 'project', value: 'Project' },
    { key: 'label', value: 'Label' },
  ],
  automatedProcessCost: 0,
  clusters: [],
  dateRangeOptions: [],
  templateOptions: [],
  labelOptions: [],
  manualCostAutomation: 0,
  organizationOptions: [],
  instanceOptions: [],
  projectOptions: [],
  loading: 'idle',
  error: false,
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
        state.projectOptions = payload.projects;
      })
      .addCase(fetchTemplateOptions.rejected, (state) => {
        state.loading = 'failed';
        state.error = true;
      })
      .addCase(setAutomatedProcessCost.fulfilled, (state, action) => {
        state.automatedProcessCost = action.payload;
      })
      .addCase(setManualProcessCost.fulfilled, (state, action) => {
        state.manualCostAutomation = action.payload;
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
export const filterRetrieveError = (state: RootState) => state.filters.error;
export const projectOptions = (state: RootState) => state.filters.projectOptions;

export const filterChoicesData = createSelector(
  [instanceOptions, templateOptions, organizationOptions, labelOptions, projectOptions],
  (
    instanceOptions: FilterOptionWithId[],
    templateOptions: FilterOptionWithId[],
    organizationOptions: FilterOption[],
    labelOptions: FilterOptionWithId[],
    projectOptions: FilterOptionWithId[],
  ) => {
    return {
      instances: instanceOptions,
      job_template: templateOptions,
      organization: organizationOptions,
      project: projectOptions,
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
    project: listToDict(filterChoicesData.project),
    label: listToDict(filterChoicesData.label),
  };
});
