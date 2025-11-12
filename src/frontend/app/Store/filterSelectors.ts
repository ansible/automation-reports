import useFilterStore from './filterStore';
import { FilterOption, FilterOptionWithId } from '@app/Types';
import { listToDict } from '@app/Utils';
import { useShallow } from 'zustand/react/shallow';
import { useLabelStore, useJobTemplateStore, useOrganizationStore, useProjectStore } from '@app/Store';

export const useManualCostAutomation = () =>
  useFilterStore((state) => state.manualCostAutomation);

export const useAutomatedProcessCost = () =>
  useFilterStore((state) => state.automatedProcessCost);

export const useFilterRetrieveError = () =>
  useFilterStore((state) => state.error);

export const useFilterChoicesData = () => {
  return {
    job_template: useJobTemplateStore(state => state.options),
    label: useLabelStore(state => state.options),
    organization: useOrganizationStore(state => state.options),
    project: useProjectStore(state => state.options)
  };
};

export const useFilterLoadingData = () => {
  return {
    job_template: useJobTemplateStore(state => state.loading === 'idle' || state.loading === 'pending'),
    label: useLabelStore(state => state.loading === 'idle' || state.loading === 'pending'),
    organization: useOrganizationStore(state => state.loading === 'idle' || state.loading === 'pending'),
    project: useProjectStore(state => state.loading === 'idle' || state.loading === 'pending')
  };
};

export const useFilterChoicesDataById = () => {
  const choices = useFilterChoicesData();
  return {
    job_template: listToDict(choices.job_template) as Record<number, FilterOptionWithId>,
    organization: listToDict(choices.organization) as Record<number, FilterOption>,
    project: listToDict(choices.project) as Record<number, FilterOptionWithId>,
    label: listToDict(choices.label) as Record<number, FilterOptionWithId>
  };
};

export const useFilterOptionsById = () =>
  useFilterStore(
    useShallow((state) => listToDict(state.filterOptions) as Record<string, FilterOption>)
  );

export const useFetchData = () => {
  return {
    job_template: useJobTemplateStore(state => state.fetchData),
    label: useLabelStore(state => state.fetchData),
    organization: useOrganizationStore(state => state.fetchData),
    project: useProjectStore(state => state.fetchData)
  };
};

export const useFetchNextPage = () => {
  return {
    job_template: useJobTemplateStore(state => state.fetchNextPage),
    label: useLabelStore(state => state.fetchNextPage),
    organization: useOrganizationStore(state => state.fetchNextPage),
    project: useProjectStore(state => state.fetchNextPage)
  };
};

export const useSearch = () => {
  return {
    job_template: useJobTemplateStore(state => state.search),
    label: useLabelStore(state => state.search),
    organization: useOrganizationStore(state => state.search),
    project: useProjectStore(state => state.search)
  };
};

export const fetchOneOption = () => {
  return {
    job_template: useJobTemplateStore(state => state.fetchOne),
    label: useLabelStore(state => state.fetchOne),
    organization: useOrganizationStore(state => state.fetchOne),
    project: useProjectStore(state => state.fetchOne)
  };
};

