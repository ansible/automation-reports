import * as React from 'react';
import { useAppDispatch, useAppSelector } from '@app/hooks';
import { filterSetOptions, selectedView, setView } from '@app/Store';
import { BaseDropdown } from '@app/Components/BaseDropdown';

type ViewSelectorProps = {
  onSelect: (itemId: string | number | null) => void;
};

const ViewSelector: React.FunctionComponent<ViewSelectorProps> = (props: ViewSelectorProps) => {
  const viewChoices = useAppSelector(filterSetOptions);
  const selectedItem = useAppSelector(selectedView);
  const dispatch = useAppDispatch();
  const onSelect = (event?: React.MouseEvent, itemId?: string | number) => {
    if (itemId) {
      const viewID = typeof itemId === 'string' ? parseInt(itemId) : itemId;
      dispatch(setView(viewID));
      props.onSelect(viewID);
    } else {
      dispatch(setView(null));
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
      placeholder={'Select a report'}
      nullable={true}
    ></BaseDropdown>
  );
};

export { ViewSelector };
