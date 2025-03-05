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
  SearchInput,
} from '@patternfly/react-core';
import { MultiChoiceDropdownProps, baseDropDownDefaultProps } from '@app/Types';
import { deepClone } from '@app/Utils';

export const MultiChoiceDropdown: React.FunctionComponent<MultiChoiceDropdownProps> = (
  props: MultiChoiceDropdownProps,
) => {
  props = { ...baseDropDownDefaultProps, ...props };
  const searchInput = React.useRef<HTMLInputElement>(null);
  const pageSize = props.pageSize || 10;
  const selectContainerRef = React.useRef<HTMLDivElement>(null);
  const toggleRef = React.useRef<HTMLButtonElement>(null);
  const menuRef = React.useRef<HTMLDivElement>(null);
  const [isMenuOpen, setIsMenuOpen] = React.useState<boolean>(false);

  const [options, setOptions] = React.useState<object[]>([]);
  const [currentPage, setCurrentPage] = React.useState<number>(1);
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
    const allOptions = props?.options?.length ? (deepClone(props.options) as object[]) : [];
    const filteredOptions = allOptions
      .filter((item: object) => {
        return props?.valueKey && item[props.valueKey].toLowerCase().includes(searchValue.toLowerCase());
      })
      .splice(0, pageSize * currentPage);
    setOptions(filteredOptions);
  }, [searchValue, currentPage, props.options]);

  const onToggleClick = (ev: React.MouseEvent) => {
    ev.stopPropagation();
    setIsMenuOpen(!isMenuOpen);
  };

  const onScroll = (ev: React.UIEvent) => {
    const target = ev.target as HTMLDivElement;
    if (target.scrollHeight - target.scrollTop < target.clientHeight + 10) {
      const page = currentPage + 1;
      setCurrentPage(page);
    }
  };

  const onSearch = (value: string) => {
    if (timeoutValue) {
      clearTimeout(timeoutValue);
      setTimeoutValue(undefined);
    }

    const timeout: number = window.setTimeout(() => {
      setSearchValue(value);
    }, 250);
    setTimeoutValue(timeout);
  };

  const menuSearch = (
    <MenuSearch>
      <MenuSearchInput>
        <SearchInput
          ref={searchInput}
          value={searchValue}
          aria-label="Filter dropdown items"
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
      {...(props.selections.length > 0 && {
        badge: <Badge isRead>{props.selections.length}</Badge>,
      })}
    >
      {props.label ? <span>{props.label}</span> : ''}
    </MenuToggle>
  );

  const menu = (
    <Menu ref={menuRef} id="mixed-group-items-menu" onSelect={props.onSelect}>
      {menuSearch}
      <Divider />
      {props?.options?.length && (
        <MenuContent onScroll={onScroll}>
          <MenuList>
            {options.map((item: object) => {
              return (
                props?.idKey !== undefined &&
                props?.valueKey !== undefined && (
                  <MenuItem
                    hasCheckbox
                    isSelected={props.selections.includes(item[props.idKey])}
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
                No results found
              </MenuItem>
            )}
          </MenuList>
        </MenuContent>
      )}
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
