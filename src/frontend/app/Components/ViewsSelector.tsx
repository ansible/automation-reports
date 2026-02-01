import * as React from 'react';
import { BaseDropdown } from '@app/Components/BaseDropdown';
import useCommonStore from '@app/Store/commonStore';
import { useTranslation } from 'react-i18next';

type ViewSelectorProps = {
  onSelect: (itemId: string | number | null) => void;
};

const ViewSelector: React.FunctionComponent<ViewSelectorProps> = (props: ViewSelectorProps) => {
  const { t } = useTranslation();
  const viewChoices = useCommonStore((state) => state.filterSetOptions);
  const selectedItem = useCommonStore((state) => state.selectedView);
  const setView = useCommonStore((state) => state.setView);


  const onSelect = (event?: React.MouseEvent, itemId?: string | number) => {
    if (itemId) {
      const viewID = typeof itemId === 'string' ? parseInt(itemId) : itemId;
      setView(viewID);
      props.onSelect(viewID);
    } else {
      setView(null);
      props.onSelect(null);
    }
  };


  return (
    <BaseDropdown
      style={{ minWidth: '160px' }}
      id={'views-options-menu'}
      options={viewChoices}
      selectedItem={selectedItem}
      onSelect={onSelect}
      idKey={'id'}
      valueKey={'name'}
      placeholder={t('Select a Report')}
      nullable={true}
    ></BaseDropdown>
  );
};

export { ViewSelector };
