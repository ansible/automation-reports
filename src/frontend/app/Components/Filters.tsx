import * as React from 'react';
import {
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
import { FilterComponentProps, FilterOption, FilterProps, RequestFilter } from '@app/Types';
import FilterIcon from '@patternfly/react-icons/dist/esm/icons/filter-icon';
import '../styles/filters.scss';
import { ViewSelector } from '@app/Components/ViewsSelector';
import { formatDateTimeToDate } from '@app/Utils';
import useFilterStore from '@app/Store/filterStore';
import useCommonStore  from '@app/Store/commonStore';
import {
  useFilterChoicesData,
  useFilterChoicesDataById,
  useFilterRetrieveError,
  useFilterOptionsById,
} from '@app/Store/filterSelectors';
import {
  useViewsById,
} from '@app/Store/commonSelectors';


export const Filters: React.FunctionComponent<FilterComponentProps> = (props: FilterComponentProps) => {
  const filterOptionsList = useFilterStore((state) => state.filterOptions);
  const filterChoicesList = useFilterChoicesData();
  const viewChoices = useCommonStore((state) => state.filterSetOptions);
  const error = useFilterRetrieveError();
  const [selectedOption, selectOption] = React.useState<string | number>();
  const filterOptionsDict = useFilterOptionsById();
  const filterChoicesDataByOption = useFilterChoicesDataById();
  const [filterSelection, selectFilter] = React.useState<FilterProps>({
    organization: [],
    job_template: [],
    instances: [],
    label: [],
    project: [],
    date_range: null,
    start_date: undefined,
    end_date: undefined,
  });
  const fetchTemplateOptions = useFilterStore((state) => state.fetchTemplateOptions);
  const setView = useCommonStore((state) => state.setView);
  const allViews = useViewsById();
  const interval = React.useRef<number | undefined>(undefined);
  const refreshInterval: string = import.meta.env.DATA_REFRESH_INTERVAL_SECONDS
    ? import.meta.env.DATA_REFRESH_INTERVAL_SECONDS
    : '60';

  const setInterval = () => {
    interval.current = window.setTimeout(
      () => {
        fetchFilters().then();
      },
      parseInt(refreshInterval) * 1000,
    );
  };

  const clearInterval = () => {
    if (interval.current) {
      window.clearTimeout(interval.current);
      interval.current = undefined;
    }
  };

  const fetchFilters = async () => {
    clearInterval();
    await fetchTemplateOptions();
    setInterval();
  };

  React.useEffect(() => {
    const execute = async () => {
      await fetchFilters();
      selectOption(filterOptionsList[0].key);
    };
    execute().then();
  }, []);

  React.useEffect(() => {
    if (!filterSelection.date_range) {
      return;
    }

    if (filterSelection.date_range === 'custom' && (!filterSelection.start_date || !filterSelection.end_date)) {
      return;
    }

    const options: RequestFilter = {
      date_range: filterSelection.date_range,
    };

    for (const key of ['organization', 'instances', 'job_template', 'label', 'project']) {
      if (filterSelection[key].length > 0) {
        options[key] = filterSelection[key];
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
    selectFilter((prevState) => ({
      ...prevState,
      ['instances']: [],
      ['organization']: [],
      ['job_template']: [],
      ['project']: [],
      ['label']: [],
    }));
    setView(null);
  };

  const viewSelected = (viewId: string | number | null | undefined) => {
    if (!viewId) {
      clearFilters();
      return;
    }
    const view = allViews[viewId];
    selectFilter((prevState) => ({
      ...prevState,
      ['instances']: view?.filters?.instances ?? [],
      ['organization']: view?.filters?.organization ?? [],
      ['job_template']: view?.filters?.job_template ?? [],
      ['project']: view?.filters?.project ?? [],
      ['label']: view?.filters?.label ?? [],
      ['date_range']: view?.filters?.date_range ?? 'month_to_date',
      ['start_date']: view?.filters?.start_date ? new Date(view.filters.start_date) : undefined,
      ['end_date']: view?.filters?.end_date ? new Date(view.filters.end_date) : undefined,
    }));
  };

  const onMultiSelectionChanged = (ev: React.MouseEvent | undefined, itemId?: string | number) => {
    ev?.stopPropagation();
    if (typeof itemId === 'undefined' || !selectedOption) {
      return;
    }
    const currentState = filterSelection[selectedOption];
    const newState = currentState.includes(itemId)
      ? currentState.filter((selection: number | string) => selection !== itemId)
      : [itemId, ...currentState];
    selectFilter((prevState) => ({
      ...prevState,
      [selectedOption]: newState,
    }));
  };

  const onDateRangeChange = (range?: string, startDate?: Date, endDate?: Date) => {
    if (range && range != filterSelection.date_range) {
      const newState = range;
      const key = 'date_range';
      selectFilter((prevState) => ({
        ...prevState,
        [key]: newState,
      }));
    }
    if (startDate) {
      selectFilter((prevState) => ({
        ...prevState,
        ['start_date']: startDate,
      }));
    }
    if (endDate) {
      selectFilter((prevState) => ({
        ...prevState,
        ['end_date']: endDate,
      }));
    }
  };

  const deleteLabelGroup = (group: string | number) => {
    selectFilter((prevState) => ({
      ...prevState,
      [group]: [],
    }));
  };

  const deleteLabel = (group: string | number, key: string | number) => {
    const currentState = filterSelection[group];
    const newState = currentState.filter((selection: number | string) => selection !== key);
    selectFilter((prevState) => ({
      ...prevState,
      [group]: newState,
    }));
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
            width: '160px',
          } as React.CSSProperties
        }
      ></BaseDropdown>
    </div>
  );

  const itemsDropdown = (
    <div className="pf-v6-u-mr-md">
      <MultiChoiceDropdown
        disabled={!selectedOption || !filterChoicesList[selectedOption]?.length}
        selections={selectedOption ? filterSelection[selectedOption] : []}
        options={selectedOption ? filterChoicesList[selectedOption] : []}
        label={selectedOption ? 'Filter by ' + filterOptionsDict[selectedOption].value + 's' : ''}
        onSelect={onMultiSelectionChanged}
        style={
          {
            minWidth: '250px',
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
            {filterSelection[item.key].map((selectedItem: string | number) => {
              return (
                <Label key={selectedItem} onClose={() => deleteLabel(item.key, selectedItem)}>
                  {filterChoicesDataByOption?.[item?.key]?.[selectedItem]?.value}
                </Label>
              );
            })}
          </LabelGroup>
        );
      })}
      <ToolbarItem>
        {(filterSelection.organization.length > 0 ||
          filterSelection.instances.length > 0 ||
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

  const toolBar = (
    <Toolbar id="filter-toolbar" clearAllFilters={clearFilters} className='pf-v6-l-flex pf-m-row-gap-md pf-v6-u-pb-0'>
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
          <ToolbarItem className='pf-v6-u-mr-0'>{dateRangePicker}</ToolbarItem>
          <AddEditView filters={filterSelection} onViewDelete={clearFilters}></AddEditView>
        </ToolbarGroup>
      </ToolbarContent>
      {<ToolbarContent>{filterLabels}</ToolbarContent>}
    </Toolbar>
  );

  return (
    <div>
      <React.Fragment>{!error && toolBar}</React.Fragment>
    </div>
  );
};
