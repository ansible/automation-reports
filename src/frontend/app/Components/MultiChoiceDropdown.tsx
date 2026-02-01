import * as React from 'react';
import {
  Badge,
  Divider,
  Menu,
  MenuContent,
  MenuItem,
  MenuList,
  MenuSearch,
  MenuSearchInput,
  MenuToggle,
  Popper,
  SearchInput, Spinner
} from '@patternfly/react-core';
import { MultiChoiceDropdownProps, baseDropDownDefaultProps, FilterOptionWithId } from '@app/Types';
import { deepClone } from '@app/Utils';
import { useTranslation } from 'react-i18next';

export const MultiChoiceDropdown: React.FunctionComponent<MultiChoiceDropdownProps> = (
  props: MultiChoiceDropdownProps
) => {
  const { t } = useTranslation();
  props = { ...baseDropDownDefaultProps, ...props };
  const searchInput = React.useRef<HTMLInputElement>(null);
  const selectContainerRef = React.useRef<HTMLDivElement>(null);
  const toggleRef = React.useRef<HTMLButtonElement>(null);
  const menuRef = React.useRef<HTMLDivElement>(null);
  const [isMenuOpen, setIsMenuOpen] = React.useState<boolean>(false);
  const [options, setOptions] = React.useState<FilterOptionWithId[]>([]);
  const [searchValue, setSearchValue] = React.useState<string>('');
  const [timeoutValue, setTimeoutValue] = React.useState<number | undefined>(undefined);

  const handleMenuClickOutside = (event: MouseEvent) => {
    if (isMenuOpen && !menuRef.current?.contains(event.target as Node)) {
      setIsMenuOpen(false);
    }
  };

  React.useEffect(() => {
    setSearchValue('');
    if (isMenuOpen) {
      searchInput?.current?.focus();
    }
    window.addEventListener('click', handleMenuClickOutside);
    return () => {
      window.removeEventListener('click', handleMenuClickOutside);
    };
  }, [isMenuOpen, menuRef]);

  React.useEffect(() => {
    const allOptions = props?.options?.length ? (deepClone(props.options) as FilterOptionWithId[]) : [];
    setOptions(allOptions);
  }, [props.options]);

  const onToggleClick = (ev: React.MouseEvent) => {
    ev.stopPropagation();
    setIsMenuOpen(!isMenuOpen);
  };

  const onScroll = (ev: React.UIEvent) => {
    const target = ev.target as HTMLDivElement;

    if (target.scrollHeight - target.scrollTop < target.clientHeight + 10) {
      if (props.onReachBottom && !props.loading) {
        props.onReachBottom();
      }
    }
  };

  const onSearch = (value: string) => {
    setSearchValue(value);
    if (timeoutValue) {
      clearTimeout(timeoutValue);
      setTimeoutValue(undefined);
    }
    const timeout: number = window.setTimeout(() => {
      if (props.onSearch) {
        props.onSearch(value?.length ? value : null);
      }
    }, 250);
    setTimeoutValue(timeout);
  };

  const menuSearch = (
    <MenuSearch>
      <MenuSearchInput>
        <SearchInput
          ref={searchInput}
          value={searchValue}
          aria-label={t('Filter dropdown items')}
          onChange={(_event, value) => onSearch(value)}
        />
      </MenuSearchInput>
    </MenuSearch>
  );

  const itemsToggle = (
    <MenuToggle
      ref={toggleRef}
      disabled={props.disabled}
      onClick={onToggleClick}
      icon={props?.icon && props.icon}
      style={props?.style}
      isExpanded={isMenuOpen}
      {...(props.selections.length > 0 ? {
        badge: <Badge isRead>{props.selections.length}</Badge>
      } : null)}
    >
      {props.label ? <span>{props.label}</span> : ''}
    </MenuToggle>
  );

  const menu = (
    <Menu ref={menuRef} id="mixed-group-items-menu" onSelect={props.onSelect}>
      {menuSearch}
      <Divider />

      <MenuContent onScroll={onScroll}>
        <MenuList>
          {props.loading}
          {options.map((item: object) => {
            return (
              props?.idKey !== undefined &&
              props?.valueKey !== undefined && (
                <MenuItem
                  hasCheckbox
                  isSelected={
                    (props.selections.findIndex((obj) =>
                      props?.idKey && obj[props.idKey] === item[props.idKey])) > -1
                  }
                  key={item[props.idKey]}
                  itemId={item[props.idKey]}
                >
                  {item[props.valueKey]}
                </MenuItem>
              )
            );
          })}
          {options.length === 0 && (
            <MenuItem isDisabled key={'no result'}>
              {t('No results found')}
            </MenuItem>
          )}
          {props.loading && (
            <div className={'dropdown-loader'}>
              <Spinner className={'spinner'} diameter="20px" aria-label={t('Loader')} />
            </div>
          )}
        </MenuList>
      </MenuContent>

    </Menu>
  );

  const select = (
    <div ref={selectContainerRef}>
      <Popper
        trigger={itemsToggle}
        triggerRef={toggleRef}
        popper={menu}
        popperRef={menuRef}
        appendTo={selectContainerRef.current || undefined}
        isVisible={isMenuOpen}
      />
    </div>
  );

  return <React.Fragment>{select}</React.Fragment>;
};
