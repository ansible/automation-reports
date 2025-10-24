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
    } catch {
      set({ loading: 'failed', error: true });
    }
  },
  fetchOne: async (id: number): Promise<FilterOptionWithId | null> => {
    const state = get();
    try {
      return await RestService.fetchFilterOption(state.endPoint, id);
    } catch {
      return null;
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
  endPoint: 'api/v1/templates/'
}));

const useLabelStore = create<FilterOptionsState & FilterOptionActions>()((a, b, state) => ({
  ...createActions(a, b, state),
  endPoint: 'api/v1/labels/'
}));

const useOrganizationStore = create<FilterOptionsState & FilterOptionActions>()((a, b, state) => ({
  ...createActions(a, b, state),
  endPoint: 'api/v1/organizations/'
}));

const useProjectStore = create<FilterOptionsState & FilterOptionActions>()((a, b, state) => ({
  ...createActions(a, b, state),
  endPoint: 'api/v1/projects/'
}));

export { useJobTemplateStore, useLabelStore, useOrganizationStore, useProjectStore };

