import { useCommonStore } from './commonStore';
import { listToDict } from '@app/Utils';

export const useCurrencyOptions = () => useCommonStore((state) => state.currencyOptions);
export const useSelectedCurrency = () => useCommonStore((state) => state.selectedCurrency);
export const useFilterSetOptions = () => useCommonStore((state) => state.filterSetOptions);
export const useSelectedView = () => useCommonStore((state) => state.selectedView);
export const useEnableTemplateCreationTime = () => useCommonStore((state) => state.enableTemplateCreationTime);
export const useViewSavingProcess = () => useCommonStore((state) => state.viewSavingProcess);
export const useViewSaveError = () => useCommonStore((state) => state.viewSaveError);

export const useCurrenciesById = () => {
  const currencies = useCurrencyOptions();
  return listToDict(currencies, 'id');
};

export const useCurrencySign = () => {
  const currencies = useCurrenciesById();
  const selected = useSelectedCurrency();
  if (selected && selected > 0) {
    const currency = currencies[selected];
    return currency?.symbol || currency?.iso_code;
  }
};

export const useViewsById = () => {
  const views = useFilterSetOptions();
  return listToDict(views, 'id');
};
