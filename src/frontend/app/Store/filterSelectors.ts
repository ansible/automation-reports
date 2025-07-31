import useFilterStore from './filterStore';
import { FilterOption, FilterOptionWithId } from '@app/Types';
import { listToDict } from '@app/Utils';
import { useShallow } from 'zustand/react/shallow';

export const useFilterOptions = () =>
  useFilterStore((state) => state.filterOptions);

export const useInstanceOptions = () =>
  useFilterStore((state) => state.instanceOptions);

export const useTemplateOptions = () =>
  useFilterStore((state) => state.templateOptions);

export const useOrganizationOptions = () =>
  useFilterStore((state) => state.organizationOptions);

export const useLabelOptions = () =>
  useFilterStore((state) => state.labelOptions);

export const useProjectOptions = () =>
  useFilterStore((state) => state.projectOptions);

export const useManualCostAutomation = () =>
  useFilterStore((state) => state.manualCostAutomation);

export const useAutomatedProcessCost = () =>
  useFilterStore((state) => state.automatedProcessCost);

export const useFilterRetrieveError = () =>
  useFilterStore((state) => state.error);

export const useFilterLoading = () =>
  useFilterStore((state) => state.loading);

export const useFilterChoicesData = () =>
    useFilterStore(
      useShallow((state) => ({
        instances: state.instanceOptions,
        job_template: state.templateOptions,
        organization: state.organizationOptions,
        project: state.projectOptions,
        label: state.labelOptions,
      })),
);

export const useFilterChoicesDataById = () => {
  const choices = useFilterChoicesData();
  return {
    instances: listToDict(choices.instances) as Record<string, FilterOptionWithId>,
    job_template: listToDict(choices.job_template) as Record<string, FilterOptionWithId>,
    organization: listToDict(choices.organization) as Record<string, FilterOption>,
    project: listToDict(choices.project) as Record<string, FilterOptionWithId>,
    label: listToDict(choices.label) as Record<string, FilterOptionWithId>,
  };
};

export const useFilterOptionsById = () =>
  useFilterStore(
    useShallow((state) => listToDict(state.filterOptions) as Record<string, FilterOption>)
  );
