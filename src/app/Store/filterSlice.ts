import { createAsyncThunk, createSelector, createSlice } from '@reduxjs/toolkit';
import { RootState } from '@app/Store/store';
import { RestService } from '@app/Services';
import { FilterOption, FilterOptionResponse, FilterState } from '@app/Types';
import { listToDict } from '@app/Utils';

export const fetchTemplateOptions = createAsyncThunk('filters/options', async (): Promise<FilterOptionResponse> => {
  const response = await RestService.fetchTemplateOptions();
  return response.data;
});

const initialState: FilterState = {
  filterOptions: [
    { key: 'instances', value: 'Instance' },
    { key: 'templates', value: 'Template' },
    { key: 'organizations', value: 'Organization' },
  ],
  instanceOptions: [],
  templateOptions: [],
  organizationOptions: [],
  dateRangeOptions: [],
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
        state.templateOptions = payload.templates;
        state.organizationOptions = payload.organizations;
        state.dateRangeOptions = payload.date_ranges;
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
export const dateRangeOptions = (state: RootState) => state.filters.dateRangeOptions;

export const filterChoicesData = createSelector(
  [instanceOptions, templateOptions, organizationOptions],
  (instanceOptions: FilterOption[], templateOptions: FilterOption[], organizationOptions: FilterOption[]) => {
    return {
      instances: instanceOptions,
      templates: templateOptions,
      organizations: organizationOptions,
    };
  },
);

export const filterOptionsById = createSelector([filterOptions], (filterOptions) => listToDict(filterOptions));

export const filterChoicesDataById = createSelector([filterChoicesData], (filterChoicesData) => {
  return {
    instances: listToDict(filterChoicesData.instances),
    templates: listToDict(filterChoicesData.templates),
    organizations: listToDict(filterChoicesData.organizations),
  };
});
