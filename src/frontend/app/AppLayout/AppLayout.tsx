import * as React from 'react';
import { Button, Dropdown, DropdownItem, DropdownList, HelperText, HelperTextItem, Icon, Masthead, MastheadBrand, MastheadContent, MastheadLogo, MastheadMain, MenuToggle, MenuToggleElement, Modal, ModalBody, ModalFooter, ModalHeader, Page, Spinner, ToolbarItem } from '@patternfly/react-core';
import { useAuthStore } from '@app/Store/authStore';
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RestService } from '@app/Services';
import useFilterStore from '@app/Store/filterStore';
import { CogsIcon, ExchangeAltIcon, PlusCircleIcon } from '@patternfly/react-icons';

interface IAppLayout {
  children: React.ReactNode;
}

type resetDataModalState = {
  isOpen: boolean,
  title: string,
  loading: boolean,
  error: boolean,
  success: boolean,
}

const AppLayout: React.FunctionComponent<IAppLayout> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());
  const myUserData = useAuthStore((state) => state.myUserData);
  const logout = useAuthStore((state) => state.logout);
  const getMyUserData = useAuthStore((state) => state.getMyUserData);
  const setReloadData = useFilterStore((state) => state.setReloadData);
  const navigate = useNavigate();
  const initialized = useRef(false);

  const [resetModalState, setResetModalState] = React.useState<resetDataModalState>(
    {
      isOpen: false,
      title: 'Restore all user inputs to defaults',
      loading: false,
      error: false,
      success: false
    }
  );

  const mastheadStyle: React.CSSProperties = {
    backgroundColor: 'var(--pf-v6-global--BackgroundColor--dark-100)',
    height: '76px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.267)',
    position: 'sticky'
  };
  const brandStyle: React.CSSProperties = {
    alignSelf: 'center',
    border: 'none'
  };
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const [isSettingsDropdownOpen, setIsSettingsDropdownOpen] = useState(false);

  const onDropdownToggle = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };
  const onDropdownSelect = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const onSettingsDropdownSelect = () => {
    setIsSettingsDropdownOpen(!isSettingsDropdownOpen);
  };


  const handleLogout = () => {
    logout().then(() => {
      navigate('/login');
    });

  };

  useEffect(() => {
    if (!initialized.current) {
      getMyUserData().then((e) => {
      }).catch((e) => {
        if (e.status == 401) {
          navigate('/login');
        }
      });
      initialized.current = true;
    }
  }, []);

  const showResetDataModal = () => {
    const modalState = { ...resetModalState };
    modalState.isOpen = true;
    setResetModalState(modalState);
  };

  const closeResetDataModal = () => {
    const modalState = { ...resetModalState };
    modalState.isOpen = false;
    modalState.loading = false;
    modalState.error = false;
    modalState.success = false;
    setResetModalState(modalState);
  };

  const resetData = () => {
    const modalState = { ...resetModalState };
    modalState.loading = true;
    setResetModalState(modalState);
    RestService.resetUserInputsToDefaults().then(() => {
      const modalState = { ...resetModalState };
      modalState.success = true;
      modalState.loading = false;
      setResetModalState(modalState);
      setReloadData(true);
    }).catch((e) => {
      console.error('Could not reset user inputs to defaults.', e);
      const modalState = { ...resetModalState };
      modalState.error = true;
      modalState.loading = false;
      setResetModalState(modalState);
    });
  };

  const masthead = (isAuthenticated ? (
      <Masthead style={mastheadStyle}>
        <MastheadMain style={{ alignSelf: 'stretch' }}>
          <MastheadBrand data-codemods style={brandStyle}>
            <MastheadLogo data-codemods style={{ maxHeight: 'unset' }}>
              <a href="/" aria-label="home">
                <svg
                  style={{ height: '48px' }}
                  xmlns="http://www.w3.org/2000/svg"
                  id="aap-logo_svg__Logos"
                  height="64"
                  x="0"
                  y="0"
                  viewBox="0 0 1580.6 240.9"
                >
                  <path
                    fill={'#fff'}
                    d="M251.5 146.7h12.8l29.8 72.8h-11.9l-8.4-21.3h-32.6l-8.5 21.3h-11.3zm18.7 42.5-12.7-31.9-12.7 31.9zM300.3 166.6h10.4v5.3c4.2-4.2 10-6.5 15.9-6.3 12.2 0 20.7 8.4 20.7 20.7v33.3h-10.4V188c0-8.3-5.1-13.4-13.1-13.4-5.3-.2-10.3 2.4-13.1 6.9v38.1h-10.4zM359.9 205.8c5.5 4.4 11.3 6.7 17.3 6.7 7.5 0 12.7-3.2 12.7-7.9 0-3.7-2.7-5.9-8.5-6.8l-9.6-1.4c-10.5-1.6-15.8-6.4-15.8-14.7 0-9.6 8.3-16 20.7-16 7.7-.1 15.1 2.3 21.4 6.7l-5.3 6.9c-5.8-3.9-11.1-5.5-16.8-5.5-6.3 0-10.6 2.9-10.6 7.2 0 3.9 2.5 5.7 8.7 6.6l9.6 1.4c10.5 1.6 16 6.6 16 14.8 0 9.5-9.6 16.6-22.1 16.6-9.1 0-17.4-2.7-23.2-7.8zM406.5 151.6c0-3.5 2.8-6.4 6.3-6.4 3.6-.1 6.6 2.6 6.7 6.2s-2.6 6.6-6.2 6.7h-.5c-3.5-.1-6.3-2.9-6.3-6.5m11.5 67.9h-10.4v-52.9H418zM456.6 220.4c-5.8 0-11.4-1.8-16-5.3v4.5h-10.3v-72.8l10.4-2.3v27.1c4.5-3.8 10.2-5.9 16.1-5.8 15 0 26.7 12 26.7 27.2s-11.7 27.4-26.9 27.4m-15.9-39.2v23.9c3.3 3.9 8.8 6.2 14.8 6.2 10.2 0 17.9-7.8 17.9-18.2s-7.8-18.3-17.9-18.3c-6.1 0-11.4 2.3-14.8 6.4M503.8 219.5h-10.4v-72.8l10.4-2.3zM541.5 220.5c-15.6 0-27.8-12-27.8-27.4 0-15.3 11.7-27.2 26.5-27.2 14.6 0 25.6 12.1 25.6 27.7v3H524c1.3 8.8 9 15.3 17.9 15.2 4.9.1 9.6-1.5 13.4-4.6l6.7 6.6c-5.8 4.4-13.1 6.8-20.5 6.7m-17.4-31.9h31.4c-1.6-8.1-7.8-14.1-15.5-14.1-8 0-14.3 5.7-15.9 14.1M621.5 146.7h12.8l29.7 72.8h-11.8l-8.4-21.3h-32.5l-8.5 21.3h-11.3zm18.8 42.5-12.7-31.9-12.7 31.9zM678.4 198c0 8.3 5.1 13.5 13.1 13.5 5.3.1 10.2-2.5 13-7v-38H715v52.9h-10.4v-5.3c-4.2 4.2-10 6.5-15.9 6.4-12.2 0-20.6-8.5-20.6-20.8v-33.1h10.4zM734.1 175.3h-11.2v-8.7h11.2v-13.5l10.3-2.5v16H760v8.7h-15.6V204c0 5.4 2.2 7.4 7.8 7.4 2.6.1 5.2-.4 7.6-1.2v8.7c-3.2 1-6.5 1.5-9.9 1.6-10.3 0-15.8-4.9-15.8-14zM791.7 165.6c15.2 0 27.5 12.4 27.5 27.6s-12.4 27.5-27.6 27.5-27.5-12.4-27.5-27.6c-.2-15 11.9-27.3 26.9-27.4.3-.1.5-.1.7-.1M809 193c0-10.3-7.7-18.3-17.3-18.3s-17.4 8-17.4 18.3 7.6 18.4 17.4 18.4c9.6 0 17.3-8.1 17.3-18.4M829 166.6h10.4v5c3.9-4 9.3-6.1 14.9-6 7.2 0 13 3.3 16.3 8.8 4.1-5.7 10.8-9.1 17.9-8.8 11.7 0 19.9 8.4 19.9 20.7v33.3H898V188c0-8.3-4.7-13.4-12.2-13.4-5.2 0-9.4 2.4-12.4 7.1.3 1.5.4 3 .4 4.6v33.3h-10.3V188c0-8.3-4.7-13.4-12.2-13.4-4.9-.1-9.4 2.3-12 6.4v38.5H829zM917.6 204.4c0-10 8.1-16.1 21.4-16.1 5 0 9.9 1 14.5 2.9v-5.6c0-7.5-4.5-11.2-12.9-11.2-4.9 0-9.9 1.4-16.4 4.5l-3.8-7.8c7.9-3.8 14.8-5.4 21.7-5.4 13.7 0 21.6 6.8 21.6 18.9v35h-10.2V215c-4.6 3.7-10.5 5.7-16.4 5.5-11.6 0-19.5-6.6-19.5-16.1m21.9 8.4c5.1.2 10.1-1.6 14-5v-9.2c-4.2-2.2-8.9-3.3-13.6-3.2-7.6 0-12.3 3.4-12.3 8.7 0 5.1 4.8 8.7 11.9 8.7M980.5 175.3h-11.2v-8.7h11.2v-13.5l10.3-2.5v16h15.6v8.7h-15.6V204c0 5.4 2.2 7.4 7.8 7.4 2.6.1 5.2-.4 7.6-1.2v8.7c-3.2 1-6.5 1.5-9.9 1.6-10.3 0-15.8-4.9-15.8-14zM1012.9 151.6c0-3.5 2.8-6.4 6.3-6.4 3.6-.1 6.6 2.6 6.7 6.2s-2.6 6.6-6.2 6.7h-.5c-3.5-.1-6.3-2.9-6.3-6.5m11.6 67.9h-10.4v-52.9h10.4zM1061.9 165.6c15.2 0 27.5 12.4 27.5 27.6s-12.4 27.5-27.6 27.5-27.5-12.4-27.5-27.6c-.2-15 11.9-27.3 26.9-27.4.2-.1.5-.1.7-.1m17.3 27.4c0-10.3-7.7-18.3-17.3-18.3s-17.4 8-17.4 18.3 7.6 18.4 17.4 18.4c9.6 0 17.3-8.1 17.3-18.4M1099.2 166.6h10.4v5.3c4.2-4.2 10-6.5 15.9-6.3 12.2 0 20.7 8.4 20.7 20.7v33.3h-10.4V188c0-8.3-5.1-13.4-13.1-13.4-5.3-.2-10.3 2.4-13.1 6.9v38.1h-10.4zM1176.1 146.7h33.7c14.2 0 23.8 8.8 23.8 21.8 0 12.8-9.7 21.6-23.8 21.6H1187v29.3h-10.9zm10.9 9.6V181h21.6c8.5 0 13.9-4.8 13.9-12.4s-5.4-12.3-13.9-12.3zM1254 219.5h-10.4v-72.8l10.4-2.3zM1263.6 204.4c0-10 8.1-16.1 21.4-16.1 5 0 9.9 1 14.5 2.9v-5.6c0-7.5-4.5-11.2-12.9-11.2-4.9 0-9.9 1.4-16.4 4.5l-3.8-7.8c7.9-3.8 14.8-5.4 21.7-5.4 13.7 0 21.6 6.8 21.6 18.9v35h-10.2V215c-4.6 3.7-10.5 5.7-16.4 5.5-11.6 0-19.5-6.6-19.5-16.1m21.9 8.4c5.1.2 10.1-1.6 14-5v-9.2c-4.2-2.2-8.9-3.3-13.6-3.2-7.6 0-12.3 3.4-12.3 8.7 0 5.1 4.8 8.7 11.9 8.7M1326.4 175.3h-11.2v-8.7h11.2v-13.5l10.3-2.5v16h15.6v8.7h-15.6V204c0 5.4 2.2 7.4 7.8 7.4 2.6.1 5.2-.4 7.6-1.2v8.7c-3.2 1-6.5 1.5-9.9 1.6-10.3 0-15.8-4.9-15.8-14zM1368.9 166.6v-8c0-11 6.3-17 18-17q3.75 0 7.5.9v9q-3.15-1.05-6.6-.9c-5.7 0-8.5 2.6-8.5 8.2v7.8h15.1v8.7h-15.1v44.2h-10.4v-44.2h-12.3v-8.7zM1425.3 165.6c15.2 0 27.5 12.4 27.5 27.6s-12.4 27.5-27.6 27.5-27.5-12.4-27.5-27.6c-.2-15 11.9-27.3 26.9-27.4.3-.1.5-.1.7-.1m17.3 27.4c0-10.3-7.7-18.3-17.3-18.3s-17.4 8-17.4 18.3 7.6 18.4 17.4 18.4c9.6 0 17.3-8.1 17.3-18.4M1462.6 166.6h10.4v6.8c3.1-5 8.6-8.1 14.6-7.9 1.8-.1 3.6.2 5.3.8v9.4c-2-.7-4-1.1-6.1-1.1-6.1 0-11 3.3-13.7 9.7v35.4h-10.4v-53.1zM1501.2 166.6h10.4v5c3.9-4 9.3-6.1 14.9-6 7.2 0 13 3.3 16.3 8.8 4.1-5.7 10.8-9.1 17.9-8.8 11.7 0 19.9 8.4 19.9 20.7v33.3h-10.4V188c0-8.3-4.7-13.4-12.2-13.4-5.2 0-9.4 2.4-12.4 7.1.3 1.5.4 3 .4 4.6v33.3h-10.3V188c0-8.3-4.7-13.4-12.2-13.4-4.9-.1-9.4 2.3-12 6.5v38.5h-10.4z"
                    className="aap-logo_svg__st0"
                  ></path>
                  <path
                    d="M129 85c12.5 0 30.6-2.6 30.6-17.5 0-1.1-.1-2.3-.3-3.4l-7.4-32.4c-1.7-7.1-3.2-10.4-15.7-16.6C126.4 10.2 105.3 2 99 2c-5.8 0-7.6 7.5-14.4 7.5-6.7 0-11.6-5.6-17.9-5.6-6 0-9.9 4.1-12.9 12.5 0 0-8.4 23.7-9.5 27.2-.2.6-.3 1.3-.2 1.9C44 54.8 80.3 85 129 85m32.6-11.4c1.7 8.2 1.7 9.1 1.7 10.1 0 14-15.7 21.8-36.4 21.8-46.9 0-87.8-27.4-87.8-45.5 0-2.5.5-5 1.5-7.3-16.8.8-38.6 3.8-38.6 23C2 107.2 76.6 146 135.6 146c45.3 0 56.7-20.5 56.7-36.7 0-12.7-11-27.1-30.7-35.7"
                    fill={'rgb(238, 0, 0)'}
                  ></path>
                  <path d="M161.5 73.6c1.7 8.2 1.7 9.1 1.7 10.1 0 14-15.7 21.8-36.4 21.8-46.8 0-87.7-27.4-87.7-45.5 0-2.5.5-5 1.5-7.3l3.7-9.1c-.2.6-.3 1.3-.2 1.9C44 54.8 80.3 85 129 85c12.5 0 30.6-2.6 30.6-17.5 0-1.1-.1-2.3-.3-3.4z"></path>
                  <path
                    fill={'#fff'}
                    d="M581.2 94.3c0 11.9 7.2 17.7 20.2 17.7 4-.1 8-.7 11.9-1.7V96.5c-2.5.8-5.1 1.2-7.7 1.2-5.4 0-7.4-1.7-7.4-6.7V69.8h15.6V55.6h-15.6v-18l-17 3.7v14.3H570v14.2h11.2zm-53 .3c0-3.7 3.7-5.5 9.3-5.5 3.4 0 6.8.4 10.1 1.3v7.2c-3.2 1.8-6.9 2.7-10.6 2.6-5.5 0-8.7-2.1-8.8-5.6m5.3 17.6c6 0 10.8-1.3 15.4-4.3v3.4h16.8V75.6c0-13.6-9.1-21-24.4-21-8.5 0-16.9 2-26 6.1l6.1 12.5c6.5-2.7 12-4.4 16.8-4.4 7 0 10.6 2.7 10.6 8.3v2.7c-4.1-1.1-8.4-1.6-12.6-1.6-14.3 0-22.9 6-22.9 16.7 0 9.9 7.7 17.3 20.2 17.3m-92.5-.9h18.1V82.4h30.3v28.8h18.1V37.6h-18.1v28.3h-30.3V37.6H441zm-68.9-27.9c0-8 6.3-14.1 14.6-14.1 4.3-.1 8.5 1.4 11.8 4.3V93c-3.2 3-7.4 4.6-11.8 4.4-8.2 0-14.6-6.1-14.6-14m26.6 27.8h16.8V33.9l-17 3.7v20.9c-4.3-2.5-9.2-3.7-14.2-3.7-16.2 0-28.9 12.5-28.9 28.5-.2 15.6 12.3 28.4 27.9 28.6h.5c5.4 0 10.6-1.7 14.9-4.8zm-77.2-42.7c5.4 0 9.9 3.5 11.7 8.8H310c1.7-5.5 5.9-8.8 11.5-8.8m-28.7 15c0 16.2 13.2 28.8 30.3 28.8 9.4 0 16.2-2.5 23.2-8.4l-11.3-10c-2.6 2.7-6.5 4.2-11.1 4.2-5.9.2-11.4-3.3-13.7-8.8h39.6v-4.2c0-17.7-11.9-30.4-28.1-30.4-15.8-.2-28.8 12.4-29 28.1.1.2.1.4.1.7m-29.3-30.4c6 0 9.4 3.8 9.4 8.3s-3.4 8.3-9.4 8.3h-17.9V53.1zm-36 58.1h18.1V84.4h13.8l13.9 26.8h20.2l-16.2-29.5c8.4-3.4 13.9-11.6 13.9-20.7 0-13.2-10.4-23.5-26-23.5h-37.6z"
                    className="aap-logo_svg__st0"
                  ></path>
                </svg>
              </a>
            </MastheadLogo>
          </MastheadBrand>
        </MastheadMain>
        <MastheadContent>
          <ToolbarItem className="pf-v6-u-ml-auto">
            {((myUserData?.is_platform_auditor || myUserData?.is_superuser) &&
              <Dropdown
                isOpen={isSettingsDropdownOpen}
                onSelect={onSettingsDropdownSelect}
                onOpenChange={(isOpen: boolean) => setIsSettingsDropdownOpen(isOpen)}
                popperProps={{ position: 'right' }}
                toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
                  <MenuToggle
                    style={{ marginRight: '16px' }}
                    ref={toggleRef}
                    onClick={onSettingsDropdownSelect}
                    isExpanded={isSettingsDropdownOpen}
                    aria-label={'settings-dropdown'}
                  >
                    <Icon>
                      <CogsIcon />
                    </Icon>
                  </MenuToggle>
                )}
              >
                <DropdownList>
                  {((myUserData?.is_platform_auditor || myUserData?.is_superuser) &&
                    <DropdownItem onClick={() => showResetDataModal()}>{resetModalState.title}</DropdownItem>)}
                </DropdownList>
              </Dropdown>
            )}
            <Dropdown
              isOpen={isDropdownOpen}
              onSelect={onDropdownSelect}
              onOpenChange={(isOpen: boolean) => setIsDropdownOpen(isOpen)}
              popperProps={{ position: 'right' }}
              toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
                <MenuToggle
                  ref={toggleRef}
                  onClick={onDropdownToggle}
                  isExpanded={isDropdownOpen}
                >
                  <svg className="pf-v5-svg" viewBox="0 0 496 512" fill="currentColor" aria-hidden="true" role="img" width="1em" height="1em">
                    <path
                      d="M248 8C111 8 0 119 0 256s111 248 248 248 248-111 248-248S385 8 248 8zm0 96c48.6 0 88 39.4 88 88s-39.4 88-88 88-88-39.4-88-88 39.4-88 88-88zm0 344c-58.7 0-111.3-26.6-146.5-68.2 18.8-35.4 55.6-59.8 98.5-59.8 2.4 0 4.8.4 7.1 1.1 13 4.2 26.6 6.9 40.9 6.9 14.3 0 28-2.7 40.9-6.9 2.3-.7 4.7-1.1 7.1-1.1 42.9 0 79.7 24.4 98.5 59.8C359.3 421.4 306.7 448 248 448z"></path>
                  </svg>
                  <span className="pf-v6-u-ml-md">{myUserData?.first_name}</span>
                </MenuToggle>
              )}
            >
              <DropdownList>
                <DropdownItem onClick={() => handleLogout()}>
                  Logout
                </DropdownItem>
              </DropdownList>
            </Dropdown>
          </ToolbarItem>
        </MastheadContent>
      </Masthead>
    ) : null
  );

  const pageId = 'primary-app-container';

  const resetDataModal = (
    <Modal
      isOpen={resetModalState.isOpen}
      ouiaId="ResetDataModal"
      aria-labelledby="reset-modal-title"
      aria-describedby="modal-box-body-reset-data"
      variant={'small'}
    >
      <ModalHeader title={resetModalState.title} labelId="reset-modal-title" />
      <ModalBody id="modal-box-body-reset-data">
        {(!resetModalState.loading && !resetModalState.success && !resetModalState.error &&
          <HelperText>
            <HelperTextItem variant="warning">This action will reset all user inputs to default values.</HelperTextItem>
            <HelperTextItem>Are you sure you want to continue?</HelperTextItem>
          </HelperText>
        )}
        {(!resetModalState.loading && resetModalState.error &&
          <HelperText>
            <HelperTextItem variant="error">An error occurred while resetting data. Please try again later.</HelperTextItem>
          </HelperText>
        )}
        {(!resetModalState.loading && resetModalState.success &&
          <HelperText>
            <HelperTextItem variant="success">Data reset was successful.</HelperTextItem>
          </HelperText>
        )}
        {(resetModalState.loading &&
          <div style={{ textAlign: 'center', height: '40px' }}>
            <Spinner className={'spinner'} diameter="33px" aria-label="Loader" />
          </div>
        )}
      </ModalBody>
      <ModalFooter>
        {(!resetModalState.success && !resetModalState.error &&
          <Button
            isDisabled={resetModalState.loading}
            key="confirm"
            variant="primary"
            onClick={() => resetData()
            }>
            Yes
          </Button>)}
        <Button
          isDisabled={resetModalState.loading}
          key="cancel"
          variant="link"
          onClick={() => closeResetDataModal()
          }>
          {(!resetModalState.success && !resetModalState.error && ('Cancel'))}
          {((resetModalState.success || resetModalState.error) && ('Close'))}
        </Button>
      </ModalFooter>
    </Modal>
  );

  return (
    <Page mainContainerId={pageId} masthead={masthead} sidebar={null} mainComponent={'main'} className={isAuthenticated ? '' : 'dark-background'}>
      {children}
      {resetDataModal}
    </Page>
  );
};

export { AppLayout };
