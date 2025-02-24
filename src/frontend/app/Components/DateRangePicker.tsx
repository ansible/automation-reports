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

  const [toDateValue, setToDateValue] = React.useState<Date | null | undefined>(props.dateTo);
  const [fromDateValue, setFromDateValue] = React.useState<Date | null | undefined>(props.dateFrom);
  const [endDateUserSelected, setEndDateUserSelected] = React.useState<boolean>(false);

  React.useEffect(() => {
    if (dateChoices?.length) {
      setDateChoices(dateChoices);
      if (!props.selectedRange) {
        const index = dateChoices.findIndex((v) => v.key === 'month_to_date');
        onSelectRangeSelect(undefined, index > -1 ? dateChoices[index].key : dateChoices[0].key);
      }
    }
  }, [dateChoices]);

  const onSelectRangeSelect = (ev: React.MouseEvent | undefined, range?: string | number) => {
    if (!range) {
      return;
    }

    props.onChange(ev, range.toString(), undefined, undefined);
    if (range === 'custom' && !props?.dateTo) {
      const date = new Date();
      setToDateValue(date);
      onToChange(undefined, yyyyMMddFormat(date), date, false);
    }
  };

  const onFromChange = (ev: React.FormEvent<HTMLInputElement>, inputDate: string, newFromDate?: Date) => {
    setFromDateValue(newFromDate);

    if (newFromDate && isValidDate(newFromDate) && inputDate === yyyyMMddFormat(newFromDate)) {
      props.onChange(ev, undefined, newFromDate, undefined);
    }
  };

  const onToChange = (
    ev: React.FormEvent<HTMLInputElement> | undefined,
    inputDate: string,
    newToDate?: Date,
    user = true,
  ) => {
    setToDateValue(newToDate);
    if (user) {
      setEndDateUserSelected(true);
    }
    if (
      newToDate &&
      isValidDate(newToDate) &&
      inputDate === yyyyMMddFormat(newToDate) &&
      toValidator(newToDate) === ''
    ) {
      props.onChange(ev, undefined, undefined, newToDate);
    }
  };

  const toValidator = (date: Date) => {
    return !fromDateValue || (fromDateValue && yyyyMMddFormat(date) >= yyyyMMddFormat(fromDateValue))
      ? ''
      : 'The "to" date must be after the "from" date';
  };

  const fromDate = (
    <DatePicker
      aria-label="Start date"
      placeholder="YYYY-MM-DD"
      value={fromDateValue && isValidDate(fromDateValue) ? yyyyMMddFormat(fromDateValue) : undefined}
      onChange={onFromChange}
    ></DatePicker>
  );

  const toDate = (
    <DatePicker
      aria-label="End date"
      placeholder={'NOW'}
      value={
        (!fromDateValue || !isValidDate(fromDateValue)) && !endDateUserSelected
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
