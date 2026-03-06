import { create } from 'zustand';
import { RestService } from '@app/Services';
import {
  FilterOptionResponse,
  FilterState,
} from '@app/Types';

import useCommonStore from './commonStore';

type FilterStoreState = FilterState & {
  loading: 'idle' | 'pending' | 'succeeded' | 'failed';
  error: boolean;
  reloadData: boolean;
};

type FilterStoreActions = {
  fetchTemplateOptions: () => Promise<void>;
  setMonthlySubscriptionCost: (cost: number) => void;
  setManualProcessCostPerHour: (cost: number) => void;
  setReloadData: (value: boolean) => void;
};

const useFilterStore = create<FilterStoreState & FilterStoreActions>((set) => ({
  filterOptions: [
    { key: 'label', value: 'Label' },
    { key: 'organization', value: 'Organization' },
    { key: 'project', value: 'Project' },
    { key: 'job_template', value: 'Template' },
  ],
  monthlySubscriptionCost: 0,
  clusters: [],
  dateRangeOptions: [],
  manualCostAutomationPerHour: 0,
  loading: 'idle',
  error: false,
  reloadData: false,
  max_pdf_job_templates: 0,

  fetchTemplateOptions: async () => {
    const { setCurrencies, setDefaultCurrency, setFilterViews, setEnableTemplateCreationTime } =
      useCommonStore.getState();

    set({ loading: 'pending', error: false });
    try {
      const response = await RestService.fetchTemplateOptions();
      const data = response.data as FilterOptionResponse;

      if (data?.currencies) {
        setCurrencies(data.currencies);
      }
      if (data?.currency) {
        setDefaultCurrency(data.currency);
      }
      if (data?.filter_sets) {
        setFilterViews(data.filter_sets);
      }
      setEnableTemplateCreationTime(data.enable_template_creation_time);

      set({
        loading: 'succeeded',
        dateRangeOptions: data.date_ranges,
        manualCostAutomationPerHour: data.manual_cost_automation_per_hour,
        monthlySubscriptionCost: data.monthly_subscription_cost,
        max_pdf_job_templates: data.max_pdf_job_templates,
      });
    } catch {
      set({ loading: 'failed', error: true });
    }
  },

  setMonthlySubscriptionCost: (cost: number) => set({ monthlySubscriptionCost: cost }),
  setManualProcessCostPerHour: (cost: number) => set({ manualCostAutomationPerHour: cost }),
  setReloadData: (value: boolean) => set({ reloadData: value }),
}));

export default useFilterStore;
