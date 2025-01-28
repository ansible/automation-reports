import React, { FormEvent } from 'react';

export type DateRangePickerProps = {
  id: string;
  selectedRange: string | undefined | null;
  onChange: (
    ev: React.MouseEvent | FormEvent<HTMLInputElement> | undefined,
    range: string | undefined,
    startDate: Date | undefined,
    endDate: Date | undefined,
  ) => void;
  dateFrom: Date | undefined | null;
  dateTo: Date | undefined | null;
} & DefaultDateRangePickerProps;

type DefaultDateRangePickerProps = Partial<typeof datePickerDefaultProps>;

export const datePickerDefaultProps = {
  label: 'Dates',
  disabled: false,
};
