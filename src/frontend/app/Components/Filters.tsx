import * as React from 'react';
import {
  Alert, AlertActionCloseButton,
  Button,
  Label,
  LabelGroup,
  Split,
  SplitItem,
  Toolbar,
  ToolbarContent,
  ToolbarGroup,
  ToolbarItem,
} from '@patternfly/react-core';
import { AddEditView, BaseDropdown, DateRangePicker, MultiChoiceDropdown } from '@app/Components';
import { FilterComponentProps, FilterOption, FilterOptionWithId, FilterProps, RequestFilter } from '@app/Types';
import FilterIcon from '@patternfly/react-icons/dist/esm/icons/filter-icon';
import '../styles/filters.scss';
import { ViewSelector } from '@app/Components/ViewsSelector';
import { formatDateTimeToDate } from '@app/Utils';
import useFilterStore from '@app/Store/filterStore';
import useCommonStore from '@app/Store/commonStore';
import {
  fetchOneOption,
  useFetchData,
  useFetchNextPage,
  useFilterChoicesData,
  useFilterChoicesDataById, useFilterLoadingData,
  useFilterOptionsById,
  useFilterRetrieveError, useSearch
} from '@app/Store/filterSelectors';
import {
  useViewsById
} from '@app/Store/commonSelectors';
import { useRef } from 'react';
import { useAuthStore } from '@app/Store/authStore';
import { ExclamationCircleIcon } from '@patternfly/react-icons';

export const Filters: React.FunctionComponent<FilterComponentProps> = (props: FilterComponentProps) => {
  const filterOptionsList = useFilterStore((state) => state.filterOptions);
  const filterChoicesList = useFilterChoicesData();
  const filterLoadingData = useFilterLoadingData();
  const viewChoices = useCommonStore((state) => state.filterSetOptions);
  const error = useFilterRetrieveError();
  const [selectedOption, selectOption] = React.useState<string | number>();
  const filterOptionsDict = useFilterOptionsById();
  const filterChoicesDataByOption = useFilterChoicesDataById();
  const fetchOneFilterOption = fetchOneOption();
  const fetchNextPageData = useFetchNextPage();
  const [errors, setErrors] = React.useState<string[]>([]);
  const [filterSelection, selectFilter] = React.useState<FilterProps>({
    organization: [],
    job_template: [],
    label: [],
    project: [],
    date_range: null,
    start_date: undefined,
    end_date: undefined
  });
  const fetchTemplateOptions = useFilterStore((state) => state.fetchTemplateOptions);
  const fetchFilterOptionsData = useFetchData();
  const searchOptions = useSearch();

  const setView = useCommonStore((state) => state.setView);
  const allViews = useViewsById();

  const hasFetched = useRef(false);
  const getMyUserData = useAuthStore((state) => state.getMyUserData);
  const reloadData = useFilterStore((state)=>state.reloadData);

  const fetchFilters = async () => {
    await fetchTemplateOptions();
    await Promise.all(filterOptionsList.map(async (option) => {
      if (fetchFilterOptionsData[option.key]) {
        try {
          await fetchFilterOptionsData[option.key]();
        }catch(e){
          setErrors((errors) => [...errors, (e as { message?: string })?.message ?? 'Something went wrong. Please try again later.']);
        }
      }
    }));
  };

  const dateChoices = useFilterStore((state) => state.dateRangeOptions);

  React.useEffect(() => {
    const execute = async () => {
      await fetchFilters();
      await getMyUserData();
      let index = filterOptionsList.findIndex((v) => v.key === 'job_template');
      index = index >= 0 ? index : 0;
      selectOption(filterOptionsList[index].key);
    };
    if (!hasFetched.current) {
      execute().then();
      hasFetched.current = true;
    }
  }, []);

  React.useEffect(() => {
    const execute = async () => {
      await fetchFilters();
    };
    if (reloadData){
      execute().then();
    }
  }, [reloadData]);

  React.useEffect(() => {
    if (!filterSelection.date_range) {
      return;
    }

    if (filterSelection.date_range === 'custom' && (!filterSelection.start_date || !filterSelection.end_date)) {
      return;
    }

    const options: RequestFilter = {
      date_range: filterSelection.date_range
    };

    for (const key of ['organization', 'job_template', 'label', 'project']) {
      if (filterSelection[key].length > 0) {
        options[key] = filterSelection[key].map((a: FilterOptionWithId) => a.key);
      }
    }

    if (filterSelection.date_range === 'custom') {
      if (filterSelection.start_date) {
        options.start_date = formatDateTimeToDate(filterSelection.start_date);
      }
      if (filterSelection.end_date) {
        options.end_date = formatDateTimeToDate(filterSelection.end_date);
      }
    }
    props.onChange(options);
  }, [filterSelection]);

  const onSelectOptionsMenu = (_event?: React.MouseEvent, itemId?: string | number) => {
    if (itemId && itemId !== selectedOption) {
      selectOption(itemId);
    }
  };

  const clearFilters = () => {
    let range: string |  null = null;
    if (dateChoices?.length) {
      const index = dateChoices.findIndex((v) => v.key === 'month_to_date');
      range = (index > -1 ? dateChoices[index].key : dateChoices[0].key).toString();
    }
    const filters = {
      organization: [],
      job_template: [],
      label: [],
      project: [],
      date_range: range,
      start_date: undefined,
      end_date: undefined
    } as FilterProps;
    selectFilter(()=>filters);
    setView(null);
  };

  const viewSelected = async (viewId: string | number | null | undefined) => {
    if (!viewId) {
      clearFilters();
      return;
    }
    const view = allViews[viewId];
    const filterOptions = ['organization', 'job_template', 'label', 'project'];
    const viewOptions = {};
    await Promise.all(filterOptions.map(async (option) => {
      viewOptions[option] = [];
      if (view.filters?.[option]?.length) {
        await Promise.all(view.filters[option].map(async (key: number) => {
          let value = filterChoicesDataByOption[option][key];
          if (value) {
            viewOptions[option].push(value);
          } else {
            try {
              value = await fetchOneFilterOption[option](key);
            } catch(e){
              setErrors((errors) => [...errors, (e as { message?: string })?.message ?? 'Something went wrong. Please try again later.']);
            }
            if (value) {
              viewOptions[option].push(value);
            }
          }
        }));
      }
    }));
    selectFilter((prevState) => ({
      ...prevState,
      ['organization']: viewOptions?.['organization'] ?? [],
      ['job_template']: viewOptions?.['job_template'] ?? [],
      ['project']: viewOptions?.['project'] ?? [],
      ['label']: viewOptions?.['label'] ?? [],
      ['date_range']: view?.filters?.date_range ?? 'month_to_date',
      ['start_date']: view?.filters?.start_date ? new Date(view.filters.start_date) : undefined,
      ['end_date']: view?.filters?.end_date ? new Date(view.filters.end_date) : undefined
    }));
  };

  const onMultiSelectionChanged = (ev: React.MouseEvent | undefined, itemId?: string | number) => {
    ev?.stopPropagation();
    if (typeof itemId === 'undefined' || !selectedOption) {
      return;
    }
    const currentState = filterSelection[selectedOption];
    const item = JSON.parse(JSON.stringify(filterChoicesDataByOption[selectedOption][itemId]));
    const newState = currentState.findIndex((v: FilterOptionWithId) => v.key === item.key) > -1
      ? currentState.filter((selection: FilterOptionWithId) => selection.key !== item.key)
      : [item, ...currentState];
    selectFilter((prevState) => ({
      ...prevState,
      [selectedOption]: newState
    }));
  };

  const onDateRangeChange = (range?: string, startDate?: Date, endDate?: Date) => {
    if (range && range != filterSelection.date_range) {
      const newState = range;
      const key = 'date_range';
      selectFilter((prevState) => ({
        ...prevState,
        [key]: newState
      }));
    }
    if (startDate) {
      selectFilter((prevState) => ({
        ...prevState,
        ['start_date']: startDate
      }));
    }
    if (endDate) {
      selectFilter((prevState) => ({
        ...prevState,
        ['end_date']: endDate
      }));
    }
  };

  const deleteLabelGroup = (group: string | number) => {
    selectFilter((prevState) => ({
      ...prevState,
      [group]: []
    }));
  };

  const deleteLabel = (group: string | number, item: FilterOptionWithId) => {
    const currentState = filterSelection[group];
    const newState = currentState.filter((selection: FilterOptionWithId) => selection.key !== item.key);
    selectFilter((prevState) => ({
      ...prevState,
      [group]: newState
    }));
  };

  const loadNextPage = async () => {
    if (selectedOption) {
      await fetchNextPageData[selectedOption]();
    }
  };

  const closeAlert = (errorIndex:number):void=>{
    const newList = [...errors];
    newList.splice(errorIndex, 1);
    setErrors(newList);
  };

  const filterSelector = (
    <div className="pf-v6-u-mr-xs">
      <BaseDropdown
        id={'filter-faceted-options-menu'}
        disabled={!filterOptionsList?.length}
        options={filterOptionsList}
        selectedItem={selectedOption}
        onSelect={onSelectOptionsMenu}
        icon={<FilterIcon />}
        style={
          {
            width: '160px'
          } as React.CSSProperties
        }
      ></BaseDropdown>
    </div>
  );

  const itemsDropdown = (
    <div className="pf-v6-u-mr-md">
      <MultiChoiceDropdown
        selections={selectedOption ? filterSelection[selectedOption] : []}
        options={selectedOption ? filterChoicesList[selectedOption] : []}
        label={selectedOption ? 'Filter by ' + filterOptionsDict[selectedOption].value + 's' : ''}
        loading={selectedOption ? filterLoadingData[selectedOption] : false}
        onSelect={onMultiSelectionChanged}
        onSearch={selectedOption ? searchOptions[selectedOption] : undefined}
        onReachBottom={loadNextPage}
        style={
          {
            minWidth: '250px'
          } as React.CSSProperties
        }
      ></MultiChoiceDropdown>
    </div>
  );

  const dateRangePicker = (
    <DateRangePicker
      id={'filter-faceted-date-range'}
      selectedRange={filterSelection.date_range}
      onChange={onDateRangeChange}
      dateFrom={filterSelection.start_date}
      dateTo={filterSelection.end_date}
      label={'Duration'}
    ></DateRangePicker>
  );

  const filterLabels = (
    <ToolbarGroup variant={'label-group'}>
      {filterOptionsList.map((item: FilterOption) => {
        return (
          <LabelGroup
            className={'pf-v6-u-mb-md'}
            key={item.key}
            categoryName={item.value}
            isClosable={true}
            onClick={() => deleteLabelGroup(item.key)}
          >
            {filterSelection[item.key].map((selectedItem: FilterOptionWithId) => {
              return (
                <Label key={selectedItem.key} onClose={() => deleteLabel(item.key, selectedItem)}>
                  {selectedItem.value}
                </Label>
              );
            })}
          </LabelGroup>
        );
      })}
      <ToolbarItem>
        {(filterSelection.organization.length > 0 ||
          filterSelection.job_template.length > 0 ||
          filterSelection.label.length > 0 ||
          filterSelection.project.length > 0) && (
          <Button variant="link" className={'pf-v6-u-mb-md'} onClick={() => clearFilters()} isInline>
            Clear all filters
          </Button>
        )}
      </ToolbarItem>
    </ToolbarGroup>
  );

    const errorElements =  (
      <div
        style={{
          marginTop: '16px',
        }}>
        {errors.map((error: string, i:number) => (
        <Alert
          style={{
             marginBottom: '16px',
          }}
          key={i}
          title={error}
          variant={'danger'}
          actionClose={<AlertActionCloseButton onClose={() => closeAlert(i)} />}>
        </Alert>))}
      </div>
  );
  const toolBar = (
    <Toolbar id="filter-toolbar" clearAllFilters={clearFilters} className="pf-v6-l-flex pf-m-row-gap-md pf-v6-u-pb-0">
      <ToolbarContent>
        <ToolbarGroup variant={'filter-group'} className="filters-wrap pf-v6-l-flex pf-v6-u-flex-wrap pf-m-row-gap-md">
          {viewChoices?.length > 0 && (
            <ToolbarItem>
              <ViewSelector onSelect={viewSelected}></ViewSelector>
            </ToolbarItem>
          )}
          <Split isWrappable className="row-gap pf-v6-l-flex pf-m-row-gap-sm pf-m-column-gap-md-on-xl">
            <SplitItem>
              <ToolbarItem>{filterSelector}</ToolbarItem>
            </SplitItem>
            <SplitItem>
              <ToolbarItem>{itemsDropdown}</ToolbarItem>
            </SplitItem>
          </Split>
          <ToolbarItem className="pf-v6-u-mr-0">{dateRangePicker}</ToolbarItem>
          <AddEditView filters={filterSelection} onViewDelete={clearFilters}></AddEditView>
        </ToolbarGroup>
      </ToolbarContent>
      {<ToolbarContent>{filterLabels}</ToolbarContent>}
    </Toolbar>
  );

  return (
    <div>
      <React.Fragment>{!error && (toolBar)}</React.Fragment>
      {errorElements}
    </div>
  );
};
