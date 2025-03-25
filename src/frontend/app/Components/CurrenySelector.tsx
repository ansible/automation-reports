import * as React from 'react';
import { useAppDispatch, useAppSelector } from '@app/hooks';
import { currencyOptions, selectedCurrency } from '@app/Store';
import { BaseDropdown } from '@app/Components/BaseDropdown';
import { setCurrency } from '@app/Store/commonSlice';
const CurrencySelector: React.FunctionComponent = () => {
  const currencyChoices = useAppSelector(currencyOptions);
  const selectedItem = useAppSelector(selectedCurrency);
  const dispatch = useAppDispatch();
  const onSelect = (_event?: React.MouseEvent, itemId?: string | number | undefined) => {
    if (itemId) {
      const currencyId = typeof itemId === 'string' ? parseInt(itemId) : itemId;
      dispatch(setCurrency(currencyId));
    }
  };

  const filterSelector = (
    <BaseDropdown
      id={'currency-options-menu'}
      options={currencyChoices}
      selectedItem={selectedItem}
      onSelect={onSelect}
      idKey={'id'}
      valueKey={'name'}
    ></BaseDropdown>
  );

  return filterSelector;
};

export { CurrencySelector };
