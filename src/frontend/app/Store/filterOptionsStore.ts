import { create, StateCreator } from 'zustand';
import { FilterOptionsState, FilterOptionWithId } from '@app/Types';
import { RestService } from '@app/Services';

type FilterOptionActions = {
  fetchData: () => Promise<void>;
  fetchOne: (id: number) => Promise<FilterOptionWithId | null>;
  fetchNextPage: () => Promise<void>;
  search: (searchString: string | null) => Promise<void>;
  queryParams: () => object;
};

const createActions: StateCreator<FilterOptionsState & FilterOptionActions> = (set, get) => ({
  endPoint: '',
  errorMessage: '',
  errorRetrieveOneMessage: '',
  options: [],
  currentPage: 1,
  pageSize: 10,
  count: 0,
  nextPage: null,
  prevPage: null,
  searchString: null,
  error: false,
  loading: 'idle',
  queryParams: () => {
    const currentState = get();
    return {
      'page_size': currentState.pageSize,
      'page': currentState.currentPage,
      'search': currentState.searchString
    };
  },
  fetchData: async () => {
    set({ loading: 'pending', error: false });
    const state = get();
    const params = state.queryParams();

    try {
      const response = await RestService.fetchFilterOptions(state.endPoint, params);
      set({
        loading: 'succeeded',
        count: response.count,
        nextPage: response.next,
        prevPage: response.previous,
        options: state.currentPage == 1 ? response.results : [
          ...state.options,
          ...response.results
        ]
      });
    } catch(error) {
      set({ loading: 'failed', error: true });
      console.error(state.errorMessage, error);
      throw new Error(state.errorMessage);
    }
  },
  fetchOne: async (id: number): Promise<FilterOptionWithId | null> => {
    const state = get();
    set({ error: false });
    try {
      return await RestService.fetchFilterOption(state.endPoint, id);
    } catch(error) {
      set({ error: true });
      const errorMessage = state.errorRetrieveOneMessage.replace('${id}', String(id));
      console.error(errorMessage);
      throw new Error(errorMessage);
    }
  },
  fetchNextPage: async () => {
    const state = get();
    if (state.nextPage) {
      set({ loading: 'pending', error: false });
      set({ currentPage: state.currentPage + 1 });
      await state.fetchData();
    }
  },
  search: async (searchString: string | null) => {
    set({ loading: 'pending', error: false, searchString: searchString, currentPage: 1, options: [] });
    const state = get();
    await state.fetchData();
  }
});

const useJobTemplateStore = create<FilterOptionsState & FilterOptionActions>()((a, b, state) => ({
  ...createActions(a, b, state),
  endPoint: 'api/v1/templates/',
  errorMessage: 'Error retrieving job templates data.',
  errorRetrieveOneMessage: 'Error retrieving job template data with id ${id}.',
}));

const useLabelStore = create<FilterOptionsState & FilterOptionActions>()((a, b, state) => ({
  ...createActions(a, b, state),
  endPoint: 'api/v1/labels/',
  errorMessage: 'Error retrieving labels data.',
  errorRetrieveOneMessage: 'Error retrieving label data with id ${id}.',
}));

const useOrganizationStore = create<FilterOptionsState & FilterOptionActions>()((a, b, state) => ({
  ...createActions(a, b, state),
  endPoint: 'api/v1/organizations/',
  errorMessage: 'Error retrieving organizations data.',
  errorRetrieveOneMessage: 'Error retrieving organization data with id ${id}.',
}));

const useProjectStore = create<FilterOptionsState & FilterOptionActions>()((a, b, state) => ({
  ...createActions(a, b, state),
  endPoint: 'api/v1/projects/',
  errorMessage: 'Error retrieving projects data.',
  errorRetrieveOneMessage: 'Error retrieving project data with id ${id}.',
}));

export { useJobTemplateStore, useLabelStore, useOrganizationStore, useProjectStore };

