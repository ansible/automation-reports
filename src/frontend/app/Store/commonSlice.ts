import { createAsyncThunk, createSelector, createSlice } from '@reduxjs/toolkit';
import { CommonState, Currency, FilterSet, Settings } from '@app/Types';
import { RestService } from '@app/Services';
import { RootState } from '@app/Store/store';
import { listToDict } from '@app/Utils';

const getErrorMessage = (e: any): string => {
  let errorMessage = '';
  if (e?.response?.data) {
    Object.keys(e.response.data).forEach((key) => {
      e.response.data[key].forEach((error: string) => {
        errorMessage += ` ${error}`;
      });
    });
    return errorMessage;
  }
  return '';
};

export const setCurrency = createAsyncThunk('filters/currency', async (currencyID: number): Promise<Settings> => {
  const response = await RestService.setCurrency(currencyID);
  return response.data;
});

export const setCurrencies = createAsyncThunk(
  'filters/currencies',
  async (currencies: Currency[]): Promise<Currency[]> => {
    return new Promise((resolve) => resolve(currencies));
  },
);

export const setDefaultCurrency = createAsyncThunk(
  'filters/defaultCurrency',
  async (currencyID: number): Promise<number> => {
    return new Promise((resolve) => resolve(currencyID));
  },
);

export const setFilterViews = createAsyncThunk('filters/views', async (views: FilterSet[]): Promise<FilterSet[]> => {
  return new Promise((resolve) => resolve(views));
});

export const setView = createAsyncThunk('filters/view/set', async (viewID: number | null): Promise<number | null> => {
  return Promise.resolve(viewID);
});

export const saveView = createAsyncThunk('filters/view/save', async (viewData: FilterSet, api): Promise<FilterSet> => {
  let response: FilterSet;
  try {
    response = await RestService.saveView(viewData);
  } catch (e: any) {
    let errorMessage = 'Error saving view.';
    errorMessage += getErrorMessage(e);
    return Promise.reject(errorMessage);
  }
  await api.dispatch(setView(null));
  return response;
});
export const deleteView = createAsyncThunk('filters/view/delete', async (viewID: number, api): Promise<number> => {
  try {
    await RestService.deleteView(viewID);
  } catch (e: any) {
    let errorMessage = 'Error deleting view.';
    errorMessage += getErrorMessage(e);
    return Promise.reject(errorMessage);
  }
  await api.dispatch(setView(null));
  return Promise.resolve(viewID);
});

const initialState: CommonState = {
  currencyOptions: [],
  filterSetOptions: [],
  selectedCurrency: undefined,
  loading: 'idle',
  error: false,
  viewSavingProcess: false,
  viewSaveError: null,
  selectedView: null,
};

export const commonSlice = createSlice({
  name: 'common',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(setCurrencies.fulfilled, (state, action) => {
        state.currencyOptions = action.payload;
      })
      .addCase(setDefaultCurrency.fulfilled, (state, action) => {
        state.selectedCurrency = action.payload;
      })
      .addCase(setCurrency.pending, (state) => {
        state.loading = 'pending';
      })
      .addCase(setCurrency.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        const payload = action.payload as Settings;
        state.selectedCurrency = payload.value;
      })
      .addCase(setCurrency.rejected, (state) => {
        state.loading = 'failed';
        state.error = true;
      })
      .addCase(setFilterViews.fulfilled, (state, action) => {
        state.filterSetOptions = action.payload;
      })

      .addCase(saveView.pending, (state) => {
        state.viewSaveError = null;
        state.viewSavingProcess = true;
      })
      .addCase(saveView.fulfilled, (state, action) => {
        state.viewSavingProcess = false;
        const payload = action.payload as FilterSet;
        const index = state.filterSetOptions.findIndex((view) => view.id === payload.id);
        if (index > -1) {
          state.filterSetOptions[index] = payload;
        } else {
          state.filterSetOptions.push(payload);
        }
        state.selectedView = payload.id;
      })
      .addCase(saveView.rejected, (state, action) => {
        state.viewSavingProcess = false;
        state.viewSaveError = action?.error?.message ?? 'Error saving view';
      })
      .addCase(deleteView.pending, (state) => {
        state.viewSaveError = null;
        state.viewSavingProcess = true;
      })
      .addCase(deleteView.fulfilled, (state, action) => {
        state.viewSavingProcess = false;
        const payload = action.payload as number;
        const index = state.filterSetOptions.findIndex((view) => view.id === payload);
        if (index > -1) {
          state.filterSetOptions.splice(index, 1);
        }
        state.selectedView = null;
      })
      .addCase(deleteView.rejected, (state, action) => {
        state.viewSavingProcess = false;
        state.viewSaveError = action?.error?.message ?? 'Error deleting view';
      })
      .addCase(setView.fulfilled, (state, action) => {
        state.selectedView = action.payload;
      });
  },
});

export default commonSlice.reducer;

export const currencyOptions = (state: RootState) => state.common.currencyOptions;
export const selectedCurrency = (state: RootState) => state.common.selectedCurrency;
export const currenciesById = createSelector([currencyOptions], (currencyOptions) => listToDict(currencyOptions, 'id'));
export const currencySign = createSelector([currenciesById, selectedCurrency], (currenciesById, selectedCurrency) => {
  if (selectedCurrency && selectedCurrency > 0) {
    const currency = currenciesById[selectedCurrency];
    if (currency) {
      return currency?.symbol ? currency.symbol : currency.iso_code;
    }
  }
});

export const viewSavingProcess = (state: RootState) => state.common.viewSavingProcess;
export const viewSaveError = (state: RootState) => state.common.viewSaveError;
export const filterSetOptions = (state: RootState) => state.common.filterSetOptions;
export const selectedView = (state: RootState) => state.common.selectedView;

export const viewsById = createSelector([filterSetOptions], (viewOptions) => listToDict(viewOptions, 'id'));
