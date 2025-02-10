import * as React from 'react';
import { BaseDropdown } from '@app/Components/BaseDropdown';
import { DateRangePickerProps, FilterOption, datePickerDefaultProps } from '@app/Types';

import { DatePicker, Flex, FlexItem, isValidDate, yyyyMMddFormat } from '@patternfly/react-core';
import { useAppSelector } from '@app/hooks';
import { dateRangeOptions } from '@app/Store';

export const DateRangePicker: React.FunctionComponent<DateRangePickerProps> = (props: DateRangePickerProps) => {
  props = { ...datePickerDefaultProps, ...props };
  const dateChoices = useAppSelector(dateRangeOptions);
  const [dateOptions, setDateChoices] = React.useState<FilterOption[]>([]);

  React.useEffect(() => {
    if (dateChoices?.length) {
      setDateChoices(dateChoices);
      if (!props.selectedRange) {
        onSelectRangeSelect(undefined, dateChoices[0].key);
      }
    }
  }, [dateChoices]);

  const onSelectRangeSelect = (ev: React.MouseEvent | undefined, range?: string | number) => {
    if (!range) {
      return;
    }
    props.onChange(ev, range.toString(), undefined, undefined);
  };

  const onFromChange = (ev: React.FormEvent<HTMLInputElement>, inputDate: string, newFromDate?: Date) => {
    if (newFromDate && isValidDate(newFromDate) && inputDate === yyyyMMddFormat(newFromDate)) {
      props.onChange(ev, undefined, newFromDate, undefined);
    }
  };

  const onToChange = (ev: React.FormEvent<HTMLInputElement>, inputDate: string, newToDate?: Date) => {
    if (
      newToDate &&
      isValidDate(newToDate) &&
      inputDate === yyyyMMddFormat(newToDate) &&
      props?.dateFrom &&
      toValidator(newToDate) === ''
    ) {
      props.onChange(ev, undefined, undefined, newToDate);
    }
  };

  const toValidator = (date: Date) => {
    return props?.dateFrom && props.dateFrom && yyyyMMddFormat(date) >= yyyyMMddFormat(props.dateFrom)
      ? ''
      : 'The "to" date must be after the "from" date';
  };

  const fromDate = (
    <DatePicker
      aria-label="Start date"
      placeholder="YYYY-MM-DD"
      value={props.dateFrom && isValidDate(props.dateFrom) ? yyyyMMddFormat(props.dateFrom) : undefined}
      onChange={onFromChange}
    ></DatePicker>
  );

  const toDate = (
    <DatePicker
      aria-label="End date"
      placeholder="YYYY-MM-DD"
      value={props.dateTo && isValidDate(props.dateTo) ? yyyyMMddFormat(props.dateTo) : undefined}
      rangeStart={props.dateFrom && isValidDate(props.dateFrom) ? props.dateFrom : undefined}
      isDisabled={!props.dateFrom || !isValidDate(props.dateFrom)}
      validators={[toValidator]}
      onChange={onToChange}
    ></DatePicker>
  );

  const rangeSelector = (
    <BaseDropdown
      id={'range-dropdown-' + props.id}
      options={dateOptions}
      disabled={props.disabled || !dateOptions?.length}
      selectedItem={props.selectedRange}
      onSelect={onSelectRangeSelect}
      style={
        {
          width: '150px',
        } as React.CSSProperties
      }
    ></BaseDropdown>
  );

  return (
    <Flex>
      <FlexItem>{props.label}</FlexItem>
      <FlexItem>{rangeSelector}</FlexItem>
      <FlexItem>
        {props?.selectedRange === 'custom' && (
          <Flex>
            <FlexItem>{fromDate}</FlexItem>
            <FlexItem>to</FlexItem>
            <FlexItem>{toDate}</FlexItem>
          </Flex>
        )}
      </FlexItem>
    </Flex>
  );
};
