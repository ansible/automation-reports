import { create } from 'zustand';
import { RestService } from '@app/Services';
import { Currency, FilterSet, Settings } from '@app/Types';

export const getErrorMessage = (e: any): string => {
    let errorMessage = '';
    if (e?.response?.data) {
      try {
        Object.keys(e.response.data).forEach((key) => {
          const errors = e.response.data[key];
          if (Array.isArray(errors)) {
            errors.forEach((error: string) => {
              errorMessage += ` ${error}`;
            });
          }
        });
      } catch {
        errorMessage = 'Something went wrong.';
      }
      return errorMessage.trim();
    }
    return 'Unknown error occurred.';
};

type CommonState = {
  currencyOptions: Currency[];
  selectedCurrency?: number;
  filterSetOptions: FilterSet[];
  selectedView: number | null;
  enableTemplateCreationTime: boolean;
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: boolean;
  viewSavingProcess: boolean;
  viewSaveError: string | null;
  setCurrencies: (currencies: Currency[]) => void;
  setDefaultCurrency: (currencyID: number) => void;
  setCurrency: (currencyID: number) => Promise<void>;
  setFilterViews: (views: FilterSet[]) => void;
  setView: (viewID: number | null) => void;
  saveView: (view: FilterSet) => Promise<{ error?: any }>;
  deleteView: (viewID: number) => Promise<{ error?: any }>;
  setEnableTemplateCreationTime: (val: boolean) => void;
  saveEnableTemplateCreationTime: (val: boolean) => Promise<{ error?: any }>;
};

export const useCommonStore = create<CommonState>((set, get) => ({
  currencyOptions: [],
  filterSetOptions: [],
  selectedCurrency: undefined,
  selectedView: null,
  enableTemplateCreationTime: true,
  loading: 'idle',
  error: false,
  viewSavingProcess: false,
  viewSaveError: null,

  setCurrencies: (currencies) => {
    set({ currencyOptions: currencies });
  },

  setDefaultCurrency: (currencyID) => {
    set({ selectedCurrency: currencyID });
  },

  setCurrency: async (currencyID) => {
    set({ loading: 'pending' });
    try {
      const response = await RestService.setCurrency(currencyID);
      const payload: Settings = response.data;
      set({ selectedCurrency: payload.value, loading: 'succeeded' });
    } catch {
      set({ loading: 'failed', error: true });
    }
  },

  setFilterViews: (views) => {
    set({ filterSetOptions: views });
  },

  setView: (viewID) => {
    set({ selectedView: viewID });
  },

  saveView: async (viewData) => {
    set({ viewSavingProcess: true, viewSaveError: null });

    try {
      const response = await RestService.saveView(viewData);
      const savedView = response as FilterSet;
      const existingViews = get().filterSetOptions;
      const index = existingViews.findIndex((v) => v.id === savedView.id);

      let updatedViews: FilterSet[];

      if (index !== -1) {
        updatedViews = [...existingViews];
        updatedViews[index] = savedView;
      } else {
        updatedViews = [...existingViews, savedView];
      }

      set({
        filterSetOptions: updatedViews,
        selectedView: savedView.id,
        viewSavingProcess: false,
      });
      
      return {};
    } catch (e: any) {
      const errorMessage = 'Error saving view. ' + getErrorMessage(e);
      set({
        viewSaveError: errorMessage,
        viewSavingProcess: false,
      });
      return { error: errorMessage };
    }
  },

  deleteView: async (viewID) => {
    set({ viewSaveError: null, viewSavingProcess: true });
    try {
      await RestService.deleteView(viewID);
      const remaining = get().filterSetOptions.filter((view) => view.id !== viewID);
      set({
        filterSetOptions: remaining,
        viewSavingProcess: false,
        selectedView: null,
      });
      return {};
    } catch (e: any) {
      const message = 'Error deleting view. ' + getErrorMessage(e);
      set({ viewSaveError: message, viewSavingProcess: false });
      return { error: message };
    }
  },

  setEnableTemplateCreationTime: (val) => {
    set({ enableTemplateCreationTime: val });
  },

  saveEnableTemplateCreationTime: async (val) => {
    set({ loading: 'pending' });
    try {
      await RestService.saveEnableTemplateCreationTime(val);
      set({ enableTemplateCreationTime: val, loading: 'succeeded' });
      return {};
    } catch (err: any) {
      set({ loading: 'failed', error: true });
      return { error: err };
    }
  },
}));

export default useCommonStore;
