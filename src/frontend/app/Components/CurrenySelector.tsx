import * as React from 'react';
import { BaseDropdown } from '@app/Components/BaseDropdown';
import useCommonStore from '@app/Store/commonStore';
import {
  useCurrencyOptions,
  useSelectedCurrency,
} from '@app/Store/commonSelectors';

const CurrencySelector: React.FunctionComponent = () => {
  const currencyChoices = useCurrencyOptions();
  const selectedItem = useSelectedCurrency();
  const setCurrency = useCommonStore((state) => state.setCurrency);

  const onSelect = (_event?: React.MouseEvent, itemId?: string | number | undefined) => {
    if (itemId) {
      const currencyId = typeof itemId === 'string' ? parseInt(itemId) : itemId;
      setCurrency(currencyId);
    }
  };

  const filterSelector = (
    <>
      <style>
        {`
          #currency-options-menu {
            min-width: 200px;
          }

          #currency-options-menu-toggle {
            min-width: 200px;
            background: transparent;
            @media (max-width: 1300px) {
              min-width: 250px !important;
            }
          }
        `}
      </style>
      <BaseDropdown
        id={'currency-options-menu'}
        options={currencyChoices}
        selectedItem={selectedItem}
        onSelect={onSelect}
        idKey={'id'}
        valueKey={'name'}
      ></BaseDropdown>
    </>
  );

  return filterSelector;
};

export { CurrencySelector };
