export type TextInputType = {
  id: string;
  value?: string | number | null;
  placeholder?: string;
  isDisabled?: boolean;
  type?:
    | 'text'
    | 'date'
    | 'datetime-local'
    | 'email'
    | 'month'
    | 'number'
    | 'password'
    | 'search'
    | 'tel'
    | 'time'
    | 'url';
  errorMessage?: string | null | undefined;
  onBlur: (value) => void;
  onFocus?: (event?: never) => void;
};
