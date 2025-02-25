export type DateRangePickerProps = {
  id: string;
  selectedRange: string | undefined | null;
  onChange: (range: string | undefined, startDate: Date | undefined, endDate: Date | undefined) => void;
  dateFrom: Date | undefined;
  dateTo: Date | undefined;
} & DefaultDateRangePickerProps;

type DefaultDateRangePickerProps = Partial<typeof datePickerDefaultProps>;

export const datePickerDefaultProps = {
  label: 'Dates',
  disabled: false,
};
