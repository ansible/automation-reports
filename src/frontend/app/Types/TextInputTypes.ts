export type TextInputType = {
  id: string;
  value?: string | number | null;
  placeholder?: string;
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
  onBlur: (value) => void;
}
