import * as React from 'react';
import { BaseDropdown } from '@app/Components';
import { DateRangePickerProps, FilterOption, datePickerDefaultProps } from '@app/Types';

import { DatePicker, Flex, FlexItem, isValidDate, yyyyMMddFormat } from '@patternfly/react-core';
import { useAppSelector } from '@app/hooks';
import { dateRangeOptions } from '@app/Store';

export const DateRangePicker: React.FunctionComponent<DateRangePickerProps> = (props: DateRangePickerProps) => {
  props = { ...datePickerDefaultProps, ...props };
  const dateChoices = useAppSelector(dateRangeOptions);
  const [dateOptions, setDateChoices] = React.useState<FilterOption[]>([]);

  const [toDateValue, setToDateValue] = React.useState<Date | undefined>(props.dateTo);
  const [fromDateValue, setFromDateValue] = React.useState<Date | undefined>(props.dateFrom);
  const [customRange, setCustomRange] = React.useState<string | number | undefined>(undefined);
  const [endDateUserSelected, setEndDateUserSelected] = React.useState<boolean>(false);

  React.useEffect(() => {
    if (dateChoices?.length) {
      setDateChoices(dateChoices);
      if (!props.selectedRange) {
        const index = dateChoices.findIndex((v) => v.key === 'month_to_date');
        setCustomRange(index > -1 ? dateChoices[index].key : dateChoices[0].key);
      }
    }
  }, [dateChoices]);

  React.useEffect(() => {
    if (customRange) {
      props.onChange(customRange.toString(), fromDateValue, toDateValue);
    }
    if (customRange === 'custom' && !toDateValue) {
      const toDateValue = new Date();
      onToChange(undefined, yyyyMMddFormat(toDateValue), toDateValue, false);
    }
  }, [fromDateValue, toDateValue, customRange]);

  const onFromChange = (ev: React.FormEvent<HTMLInputElement> | undefined, inputDate: string, newFromDate?: Date) => {
    if (newFromDate && isValidDate(newFromDate) && inputDate === yyyyMMddFormat(newFromDate)) {
      setFromDateValue(newFromDate);
    }
  };

  const onToChange = (
    _ev: React.FormEvent<HTMLInputElement> | undefined,
    inputDate: string,
    newToDate?: Date,
    user = true,
  ) => {
    _ev?.stopPropagation();
    if (
      newToDate &&
      isValidDate(newToDate) &&
      inputDate === yyyyMMddFormat(newToDate) &&
      toValidator(newToDate) === ''
    ) {
      setToDateValue(newToDate);
    }
    if (user) {
      setEndDateUserSelected(true);
    }
  };

  const onRangeSelect = (_ev: React.MouseEvent | undefined, range?: string | number) => {
    setCustomRange(range?.toString());
  };
  const toValidator = (date: Date): string => {
    return fromDateValue && yyyyMMddFormat(fromDateValue) > yyyyMMddFormat(date)
      ? 'The "to" date must be after the "from" date'
      : '';
  };

  const fromValidator = (date: Date): string => {
    return toDateValue && yyyyMMddFormat(toDateValue) < yyyyMMddFormat(date)
      ? 'The "from" date must be before the "to" date'
      : '';
  };

  const fromDate = (
    <DatePicker
      aria-label="Start date"
      placeholder="YYYY-MM-DD"
      value={fromDateValue && isValidDate(fromDateValue) ? yyyyMMddFormat(fromDateValue) : undefined}
      onChange={onFromChange}
      validators={[fromValidator]}
    ></DatePicker>
  );

  const toDate = (
    <DatePicker
      aria-label="End date"
      placeholder="YYYY-MM-DD"
      value={
        (!fromDateValue || !isValidDate(fromDateValue)) &&
        toDateValue &&
        isValidDate(toDateValue) &&
        !endDateUserSelected
          ? 'Now'
          : toDateValue && isValidDate(toDateValue)
            ? yyyyMMddFormat(toDateValue)
            : undefined
      }
      rangeStart={fromDateValue && isValidDate(fromDateValue) ? fromDateValue : undefined}
      isDisabled={!fromDateValue || !isValidDate(fromDateValue)}
      validators={[toValidator]}
      onChange={onToChange}
    ></DatePicker>
  );

  const rangeSelector = (
    <BaseDropdown
      id={'range-dropdown-' + props.id}
      options={dateOptions}
      disabled={props.disabled || !dateOptions?.length}
      selectedItem={customRange}
      onSelect={onRangeSelect}
      style={
        {
          width: '150px',
        } as React.CSSProperties
      }
    ></BaseDropdown>
  );

  return (
    <Flex>
      <FlexItem>{props.label}:</FlexItem>
      <FlexItem>{rangeSelector}</FlexItem>
      <FlexItem>
        {customRange === 'custom' && (
          <Flex style={{ alignItems: 'self-start' }}>
            <FlexItem>{fromDate}</FlexItem>
            <FlexItem style={{ marginTop: '8px' }}>to</FlexItem>
            <FlexItem>{toDate}</FlexItem>
          </Flex>
        )}
      </FlexItem>
    </Flex>
  );
};
