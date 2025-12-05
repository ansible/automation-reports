import { create } from 'zustand';
import { RestService } from '@app/Services';
import { Currency, FilterSet, Settings } from '@app/Types';
import { getErrorMessage } from '@app/Utils';

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
  saveView: (view: FilterSet) => Promise<void>;
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
      });
    } catch (e: any) {
      const msg = 'Error saving report. ' + getErrorMessage(e);
      throw new Error(msg);
    } finally {
      set({ viewSavingProcess: false });
    }
  },

  deleteView: async (viewID) => {
    set({ viewSaveError: null, viewSavingProcess: true });
    try {
      await RestService.deleteView(viewID);
      const remaining = get().filterSetOptions.filter((view) => view.id !== viewID);
      set({
        filterSetOptions: remaining,
        selectedView: null,
      });
      return {};
    } catch (e: any) {
      const message = 'Error deleting report. ' + getErrorMessage(e);
      throw new Error(message);
    } finally {
      set({
        viewSavingProcess: false,
      });
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
      const message = 'Error saving settings. ' + getErrorMessage(err);
      set({ loading: 'failed' });
      throw new Error(message);
    }
  },
}));

export default useCommonStore;
