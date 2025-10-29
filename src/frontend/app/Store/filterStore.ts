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
  setAutomatedProcessCost: (cost: number) => void;
  setManualProcessCost: (cost: number) => void;
  setReloadData: (value: boolean) => void;
};

const useFilterStore = create<FilterStoreState & FilterStoreActions>((set) => ({
  filterOptions: [
    { key: 'label', value: 'Label' },
    { key: 'organization', value: 'Organization' },
    { key: 'project', value: 'Project' },
    { key: 'job_template', value: 'Template' },
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
  reloadData: false,
  max_pdf_job_templates: 0,

  fetchTemplateOptions: async () => {
    const {
      setCurrencies,
      setDefaultCurrency,
      setFilterViews,
      setEnableTemplateCreationTime,
    } = useCommonStore.getState();

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
        instanceOptions: data.instances,
        labelOptions: data.labels,
        templateOptions: data.job_templates,
        organizationOptions: data.organizations,
        dateRangeOptions: data.date_ranges,
        manualCostAutomation: data.manual_cost_automation,
        automatedProcessCost: data.automated_process_cost,
        projectOptions: data.projects,
        max_pdf_job_templates: data.max_pdf_job_templates
      });
    } catch {
      set({ loading: 'failed', error: true });
    }
  },

  setAutomatedProcessCost: (cost: number) => set({ automatedProcessCost: cost }),
  setManualProcessCost: (cost: number) => set({ manualCostAutomation: cost }),
  setReloadData: (value: boolean)=> set({reloadData: value}),
}));

export default useFilterStore;
