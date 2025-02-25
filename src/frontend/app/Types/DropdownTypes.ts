import React from 'react';

export type BaseDropdownProps = {
  id: string;
  selectedItem: number | string | undefined | null;
  options: object[];
  onSelect: (ev: React.MouseEvent | undefined, itemId?: string | number) => void;
  icon?: React.ReactNode;
  style?: React.CSSProperties;
} & DefaultBaseDropdownProps;

type DefaultBaseDropdownProps = Partial<typeof baseDropDownDefaultProps>;

export const baseDropDownDefaultProps = {
  idKey: 'key',
  valueKey: 'value',
  disabled: false,
  pageSize: 10,
};

export type MultiChoiceDropdownProps = {
  selections: (number | string)[];
  options: object[];
  label?: string;
  icon?: React.ReactNode;
  onSelect: (ev: React.MouseEvent | undefined, itemId?: string | number) => void;
  style?: React.CSSProperties;
} & DefaultBaseDropdownProps;
