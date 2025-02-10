import * as React from 'react';
import {
  Button,
  LabelGroup,
  Split,
  SplitItem,
  Toolbar,
  ToolbarContent,
  ToolbarGroup,
  ToolbarItem,
} from '@patternfly/react-core';
import { useAppDispatch, useAppSelector } from '@app/hooks';
import {
  fetchTemplateOptions,
  filterChoicesData,
  filterChoicesDataById,
  filterOptions,
  filterOptionsById,
} from '@app/Store';
import { Label } from '@patternfly/react-core/src/components/Label';
import { MultiChoiceDropdown } from '@app/Components/MultiChoiceDropdown';
import { BaseDropdown } from '@app/Components/BaseDropdown';
import { DateRangePicker } from '@app/Components/DateRangePicker';
import { FilterOption } from '@app/Types';
import FilterIcon from '@patternfly/react-icons/dist/esm/icons/filter-icon';
import { FormEvent } from 'react';
import '../styles/filters.scss';
import { ParamsContext } from '@app/Store/paramsContext';
import moment from 'moment';

interface FilterProps {
  organization: (string | number)[];
  job_template: (string | number)[];
  instances: (string | number)[];
  label: (string | number)[];
  date_range: string | null;
  start_date: Date | null;
  end_date: Date | null;
}

export const Filters: React.FunctionComponent = () => {
  const filterOptionsList = useAppSelector(filterOptions);
  const filterChoicesList = useAppSelector(filterChoicesData);
  const filterOptionsDict = useAppSelector(filterOptionsById) as Record<string, FilterOption>;
  const filterChoicesDataByOption = useAppSelector(filterChoicesDataById);
  const [selectedOption, selectOption] = React.useState<string | number>();
  const [filterSelection, selectFilter] = React.useState<FilterProps>({
    organization: [],
    job_template: [],
    instances: [],
    label: [],
    date_range: null,
    start_date: null,
    end_date: null,
  });
  const context = React.useContext(ParamsContext);
  if (!context) {
    throw new Error ('Filters must be used within a ParamsProvider');
  }
  const { setParams } = context;

  const dispatch = useAppDispatch();

  React.useEffect(() => {
    const execute = async () => {
      await dispatch(fetchTemplateOptions());
      onSelectOptionsMenu(undefined, filterOptionsList[0].key);
    };
    execute().then();
  }, []);

  const onSelectOptionsMenu = (_event?: React.MouseEvent, itemId?: string | number) => {
    if (itemId && itemId !== selectedOption) {
      selectOption(itemId);
    }
  };

  const updateParams = (key, value) => {
    setParams((prevParams) => ({
      ...prevParams,
      [key]: value
    }));
  }

  const resetPagination = () => {
    updateParams("page", 1);
    updateParams("page_size", 10);
  }

  const onDateRangeChange = (
    _event?: React.MouseEvent | FormEvent<HTMLInputElement>,
    range?: string,
    startDate?: Date,
    endDate?: Date,
  ) => {
    if (range && range != filterSelection.date_range) {
      const newState = range;
      const key = 'date_range';
      selectFilter((prevState) => ({
        ...prevState,
        [key]: newState,
      }));
      if (newState !== "custom") {
        setParams((prevState) => ({
          ...prevState,
          "start_date": null,
          "end_date": null,
        }))
      }
      updateParams(key, newState);  
      resetPagination();
    }
    if (startDate) {
      selectFilter((prevState) => ({
        ...prevState,
        ['start_date']: startDate,
      }));
      const formattedDate = moment(startDate).format('YYYY-MM-DD');
      updateParams('start_date', formattedDate); 
      resetPagination();
    }
    if (endDate) {
      selectFilter((prevState) => ({
        ...prevState,
        ['end_date']: endDate,
      }));
      const formattedDate = moment(endDate).format('YYYY-MM-DD');
      updateParams('end_date', formattedDate);
      resetPagination();
    }
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
    updateParams(selectedOption, newState);
    resetPagination();
  };

  const deleteLabelGroup = (group: string | number) => {
    selectFilter((prevState) => ({
      ...prevState,
      [group]: [],
    }));
    updateParams(group, null);
    resetPagination();
  };

  const deleteLabel = (group: string | number, key: string | number) => {
    const currentState = filterSelection[group];
    const newState = currentState.filter((selection: number | string) => selection !== key);
    selectFilter((prevState) => ({
      ...prevState,
      [group]: newState,
    }));
    updateParams(group, newState);
    resetPagination();
  };

  const clearFilters = () => {
    selectFilter((prevState) => ({
      ...prevState,
      ['instances']: [],
      ['organization']: [],
      ['job_template']: [],
      ['label']: [],
    }));
    setParams((prevState) => ({
      ...prevState,
      ['instances']: null,
      ['organization']: null,
      ['job_template']: null,
      ['label']: null
    }))
  };

  const filterLabels = (
    <ToolbarGroup variant={'label-group'}>
      {filterOptionsList.map((item: FilterOption) => {
        return (
          <LabelGroup
            key={item.key}
            categoryName={item.value}
            isClosable={true}
            onClick={() => deleteLabelGroup(item.key)}
          >
            {filterSelection[item.key].map((selectedItem: string | number) => {
              return (
                <Label key={selectedItem} onClose={() => deleteLabel(item.key, selectedItem)}>
                  {filterChoicesDataByOption?.[item?.key]?.[selectedItem].value}
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
          filterSelection.label.length > 0 )
           && (
          <Button variant="link" onClick={() => clearFilters()} isInline>
            Clear all filters
          </Button>
        )}
      </ToolbarItem>
    </ToolbarGroup>
  );

  const filterSelector = (
    <div className='pf-v6-u-mr-xs'>
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
    <div className='pf-v6-u-mr-md'>
      <MultiChoiceDropdown
        disabled={!selectedOption || !filterChoicesList[selectedOption]?.length}
        selections={selectedOption ? filterSelection[selectedOption] : []}
        options={selectedOption ? filterChoicesList[selectedOption] : []}
        label={selectedOption ? 'Filter by ' + filterOptionsDict[selectedOption].value : ''}
        onSelect={onMultiSelectionChanged}
        style={
          {
            width: '220px',
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

  const toolBar = (
    <Toolbar id="filter-toolbar" clearAllFilters={clearFilters}>
      <ToolbarContent>
        <ToolbarGroup variant={'filter-group'} className='filters-wrap'>
          <Split isWrappable className='row-gap'>
            <SplitItem>
              <ToolbarItem>{filterSelector}</ToolbarItem>
            </SplitItem>

            <SplitItem>
              <ToolbarItem>{itemsDropdown}</ToolbarItem>
            </SplitItem>
          </Split>
          <ToolbarItem>{dateRangePicker}</ToolbarItem>
        </ToolbarGroup>
      </ToolbarContent>
      <ToolbarContent>{filterLabels}</ToolbarContent>
    </Toolbar>
  );

  return (
    <div className={'filters'}>
      <React.Fragment>{toolBar}</React.Fragment>
    </div>
  );
};
