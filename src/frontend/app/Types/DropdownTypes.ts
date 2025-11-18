import React from 'react';
import { FilterOptionWithId } from '@app/Types/FilterTypes';

export type BaseDropdownProps = {
  id: string;
  selectedItem: number | string | undefined | null;
  options: object[];
  onSelect: (ev: React.MouseEvent | undefined, itemId?: string | number | undefined) => void;
  icon?: React.ReactNode;
  style?: React.CSSProperties;
  placeholder?: string;
  nullable?: boolean;
} & DefaultBaseDropdownProps;

type DefaultBaseDropdownProps = Partial<typeof baseDropDownDefaultProps>;

export const baseDropDownDefaultProps = {
  idKey: 'key',
  valueKey: 'value',
  disabled: false,
  pageSize: 10,
};

export type MultiChoiceDropdownProps = {
  selections: FilterOptionWithId[];
  options: object[];
  label?: string;
  icon?: React.ReactNode;
  onSelect: (ev: React.MouseEvent | undefined, itemId?: string | number) => void;
  onSearch?: (searchString: string | null) => void;
  onReachBottom?: ()=> void;
  loading?: boolean,
  style?: React.CSSProperties;
} & DefaultBaseDropdownProps;
