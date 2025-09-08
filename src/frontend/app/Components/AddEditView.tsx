import * as React from 'react';
import {
  Alert,
  Button,
  Form,
  FormGroup,
  Menu,
  MenuContent,
  MenuItem,
  MenuList,
  MenuToggle,
  MenuToggleAction,
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalVariant,
  Popper,
  Spinner,
  TextInput,
} from '@patternfly/react-core';
import { AddEditViewProps, FilterProps } from '@app/Types';
import { deepClone, formatDateTimeToDate } from '@app/Utils';
import { FilterSet } from '@app/Types';
import useCommonStore from '@app/Store/commonStore';
import {
  useViewSaveError,
  useViewSavingProcess,
  useViewsById,
} from '@app/Store/commonSelectors';

const AddEditView: React.FunctionComponent<AddEditViewProps> = (props: AddEditViewProps) => {
  const [isModalOpen, setModalOpen] = React.useState(false);
  const [isMenuOpen, setIsMenuOpen] = React.useState<boolean>(false);
  const [modalVariant, setModalVariant] = React.useState<string>('create');
  const [filterNameValue, setFilterNameValue] = React.useState('');
  const filterSaveProcess = useViewSavingProcess();
  const filterSaveError = useViewSaveError();
  const menuRef = React.useRef<HTMLDivElement>(null);
  const toggleRef = React.useRef<HTMLButtonElement>(null);
  const containerRefDropdown = React.useRef<HTMLDivElement>(null);
  const selectedViewItem = useCommonStore((state) => state.selectedView);
  const allViews = useViewsById();

  const saveView = useCommonStore((state) => state.saveView);
  const deleteView = useCommonStore((state) => state.deleteView);

  const handleMenuClickOutside = (event: MouseEvent) => {
    if (isMenuOpen && !containerRefDropdown.current?.contains(event.target as Node)) {
      setIsMenuOpen(false);
    }
  };

  React.useEffect(() => {
    window.addEventListener('click', handleMenuClickOutside);
    return () => {
      window.removeEventListener('click', handleMenuClickOutside);
    };
  }, [isMenuOpen, containerRefDropdown]);

  const openModal = () => {
    setModalOpen(true);
  };
  const closeModal = () => {
    setModalOpen(false);
  };

  const handleFilterNameValueChange = (_event: React.FormEvent<HTMLInputElement>, value: string) => {
    setFilterNameValue(value);
  };

  const saveFilter = async () => {
    if (modalVariant === 'delete') {
      deleteView(selectedViewItem as number).then((response) => {
        if (!response?.['error']) {
          closeModal();
          props.onViewDelete();
          setModalVariant('create');
        }
      });

    } else {
      const filters = deepClone(props.filters) as FilterProps;
      const viewData = {
        name: filterNameValue,
        filters: {
          date_range: filters.date_range,
        },
      } as FilterSet;
      if (modalVariant === 'edit' && selectedViewItem) {
        viewData.id = selectedViewItem;
      }
      ['organization', 'job_template', 'label', 'project'].forEach((key) => {
        if (filters[key] && filters[key].length) {
          viewData.filters[key] = filters[key];
        }
      });
      if (filters.date_range === 'custom') {
        if (filters.start_date) {
          viewData.filters.start_date = formatDateTimeToDate(filters.start_date);
        }
        if (filters.end_date) {
          viewData.filters.end_date = formatDateTimeToDate(filters.end_date);
        }
      }

      saveView(viewData).then((response) => {
        if (!response?.['error']) {
          closeModal();
        }
      });
    }
  };

  const onSelect = (_ev: React.MouseEvent | undefined, itemId?: string | number) => {
    toggleRef?.current?.blur();

    setModalVariant(itemId?.toString() || 'create');
    if (itemId === 'create') {
      setFilterNameValue('');
    } else {
      const name = (selectedViewItem && allViews?.[selectedViewItem]?.name) || '';
      setFilterNameValue(name);
    }
    openModal();
    setIsMenuOpen(false);
  };

  const toggleClick = () => {
    if (!isMenuOpen && !selectedViewItem) {
      setFilterNameValue('');
      openModal();
      return;
    }
    setIsMenuOpen(!isMenuOpen);
  };

  const onFormSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (modalVariant === 'create' || modalVariant === 'edit') {
      saveFilter();
    }
  };

  const menu = (
    <Menu ref={menuRef} id="filter-set-menu" onSelect={onSelect}>
      <MenuContent>
        <MenuList>
          <MenuItem key="create" itemId="create">
            Create new report
          </MenuItem>
          <MenuItem isDisabled={!selectedViewItem} key="edit" itemId="edit">
            Edit current report
          </MenuItem>
          <MenuItem isDisabled={!selectedViewItem} key="delete" itemId="delete">
            Delete current report
          </MenuItem>
        </MenuList>
      </MenuContent>
    </Menu>
  );

  const menuToggle = (
    <MenuToggle
      variant="secondary"
      ref={toggleRef}
      onClick={toggleClick}
      isExpanded={isMenuOpen}
      id={'filter-set-menu-toggle'}
      aria-label={' Save as Report'}
      splitButtonItems={[
        <MenuToggleAction key="split-action-save" onClick={toggleClick} aria-label="Save" className='pf-v6-u-w-100'>
          Save as Report
        </MenuToggleAction>,
      ]}
    ></MenuToggle>
  );

  const select = (
    <div ref={containerRefDropdown} className="save-as-report pf-v6-u-mr-md">
      <Popper
        trigger={menuToggle}
        triggerRef={toggleRef}
        popper={menu}
        popperRef={menuRef}
        appendTo={containerRefDropdown.current || undefined}
        isVisible={isMenuOpen}
      />
    </div>
  );

  const modal = (
    <>
      <style>
        {`
          .modal-wrap {
            min-height: 66px;
          }
          .pf-v6-c-form.hidden {
            display: none;
          }
          .add-edit-report-modal-button:focus {
            --pf-v6-c-button--BackgroundColor: transparent;
          }
        `}
      </style>
      <Modal
        position="top"
        variant={ModalVariant.small}
        isOpen={isModalOpen}
        onClose={closeModal}
        aria-labelledby="form-modal-set-filter"
        aria-describedby="modal-box-set-filter-form"
        className='pf-v6-u-mt-4xl'
      >
        <ModalHeader
          title={modalVariant === 'create' ? 'Create report' : modalVariant === 'edit' ? 'Edit report' : 'Delete report'}
          descriptorId="modal-box-description-form"
          labelId="form-filter-set-title"
        />
        <ModalBody>
          {modalVariant !== 'delete' && (
            <div className={'modal-wrap'}>
              {filterSaveError && <Alert variant="danger" isInline title={filterSaveError} />}
              {filterSaveProcess && (
                <div className={'pf-v6-l-flex pf-m-justify-content-center pf-v6-u-py-md'}>
                  <Spinner className={'spinner'} diameter="40px" aria-label="Loader" />
                </div>
              )}
              <Form id="modal-set-view-form" className={filterSaveProcess ? 'hidden' : ''} onSubmit={onFormSubmit}>
                <FormGroup isRequired label={'Report name'}>
                  <TextInput
                    value={filterNameValue}
                    onChange={handleFilterNameValueChange}
                    autoComplete={'false'}
                    isRequired
                    type="text"
                    id="name"
                    name="name"
                    maxLength={255}
                  />
                </FormGroup>
              </Form>
            </div>
          )}
          {modalVariant === 'delete' && (
            <div className={'modal-wrap'}>Do you really want to delete the report: {filterNameValue}?</div>
          )}
        </ModalBody>
        <ModalFooter>
          <Button
            key="create"
            variant="primary"
            form="modal-set-view-form"
            isDisabled={!filterNameValue?.trim()?.length || filterSaveProcess}
            onClick={saveFilter}
            className="add-edit-report-modal-button"
          >
            {modalVariant === 'create' ? 'Create' : modalVariant === 'edit' ? 'Save' : 'Delete'}
          </Button>
          <Button className="add-edit-report-modal-button" key="cancel" variant="link" onClick={closeModal} isDisabled={filterSaveProcess}>
            Cancel
          </Button>
        </ModalFooter>
      </Modal>
    </>
  );

  return (
    <React.Fragment>
      {select}
      {modal}
    </React.Fragment>
  );
};

export { AddEditView };
