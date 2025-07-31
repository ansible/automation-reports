import * as React from 'react';
import { BaseDropdown } from '@app/Components';
import { DateRangePickerProps, FilterOption, datePickerDefaultProps } from '@app/Types';
import { DatePicker, Flex, FlexItem, isValidDate, yyyyMMddFormat } from '@patternfly/react-core';
import useFilterStore from '@app/Store/filterStore';

export const DateRangePicker: React.FunctionComponent<DateRangePickerProps> = (props: DateRangePickerProps) => {
  props = { ...datePickerDefaultProps, ...props };
  const [dateOptions, setDateChoices] = React.useState<FilterOption[]>([]);
  const dateChoices = useFilterStore((state) => state.dateRangeOptions);

  React.useEffect(() => {
    if (dateChoices?.length) {
      setDateChoices(dateChoices);
      if (!props.selectedRange) {
        const index = dateChoices.findIndex((v) => v.key === 'month_to_date');
        const range = index > -1 ? dateChoices[index].key : dateChoices[0].key;
        props.onChange(range.toString(), props.dateFrom, props.dateTo ?? new Date());
      }
    }
  }, [dateChoices]);

  const onFromChange = (ev: React.FormEvent<HTMLInputElement> | undefined, inputDate: string, newFromDate?: Date) => {
    if (newFromDate && isValidDate(newFromDate) && inputDate === yyyyMMddFormat(newFromDate)) {
      props.onChange(props.selectedRange?.toString(), newFromDate, props.dateTo);
    }
  };

  const fromValidator = (date: Date): string => {
    return props.dateTo && yyyyMMddFormat(props.dateTo) < yyyyMMddFormat(date)
      ? 'The "from" date must be before the "to" date'
      : '';
  };

  const toValidator = (date: Date): string => {
    return props.dateFrom && yyyyMMddFormat(props.dateFrom) > yyyyMMddFormat(date)
      ? 'The "to" date must be after the "from" date'
      : '';
  };

  const onToChange = (_ev: React.FormEvent<HTMLInputElement> | undefined, inputDate: string, newToDate?: Date) => {
    _ev?.stopPropagation();
    if (
      newToDate &&
      isValidDate(newToDate) &&
      inputDate === yyyyMMddFormat(newToDate) &&
      toValidator(newToDate) === ''
    ) {
      props.onChange(props.selectedRange?.toString(), props.dateFrom, newToDate);
    }
  };

  const fromDate = (
    <DatePicker
      aria-label="Start date"
      placeholder="YYYY-MM-DD"
      value={props.dateFrom && isValidDate(props.dateFrom) ? yyyyMMddFormat(props.dateFrom) : undefined}
      onChange={onFromChange}
      validators={[fromValidator]}
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

  const onRangeSelect = (_ev: React.MouseEvent | undefined, range?: string | number) => {
    props.onChange(range?.toString(), props.dateFrom, props.dateTo);
  };

  const rangeSelector = (
    <BaseDropdown
      id={'range-dropdown-' + props.id}
      options={dateOptions}
      disabled={props.disabled || !dateOptions?.length}
      selectedItem={props.selectedRange}
      onSelect={onRangeSelect}
      style={
        {
          width: '150px',
        } as React.CSSProperties
      }
    ></BaseDropdown>
  );

  return (
    <Flex style={{ alignItems: 'self-start' }}>
      <FlexItem style={{ marginTop: '8px' }}>{props.label}:</FlexItem>
      <FlexItem className="range-selector">{rangeSelector}</FlexItem>
      <FlexItem>
        {props.selectedRange === 'custom' && (
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
