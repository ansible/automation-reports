import * as React from 'react';
import { Menu, MenuContent, MenuItem, MenuList, MenuToggle, Popper } from '@patternfly/react-core';
import { listToDict } from '@app/Utils';
import { BaseDropdownProps, baseDropDownDefaultProps } from '@app/Types';

export const BaseDropdown: React.FunctionComponent<BaseDropdownProps> = (props: BaseDropdownProps) => {
  props = { ...baseDropDownDefaultProps, ...props };
  const toggleRef = React.useRef<HTMLButtonElement>(null);
  const containerRefDropdown = React.useRef<HTMLDivElement>(null);
  const menuRef = React.useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = React.useState<boolean>(false);
  const [value, setValue] = React.useState<string | null>(null);

  const toggleClick = () => {
    setIsOpen(!isOpen);
  };

  const handleMenuClickOutside = (event: MouseEvent) => {
    if (isOpen && !containerRefDropdown.current?.contains(event.target as Node)) {
      setIsOpen(false);
    }
  };

  React.useEffect(() => {
    window.addEventListener('click', handleMenuClickOutside);
    return () => {
      window.removeEventListener('click', handleMenuClickOutside);
    };
  }, [isOpen, containerRefDropdown]);

  React.useEffect(() => {
    if (props?.idKey === undefined && props?.valueKey === undefined) {
      return;
    }
    const choicesDict = listToDict(props.options, props.idKey);
    if (props?.selectedItem && choicesDict[props.selectedItem] && props.valueKey !== undefined) {
      setValue(choicesDict[props.selectedItem][props.valueKey].toString());
    } else {
      setValue(null);
    }
  }, [props.selectedItem]);

  const onSelect = (ev: React.MouseEvent | undefined, itemId?: string | number) => {
    setIsOpen(false);
    props.onSelect(ev, itemId);
  };

  const menu = (
    <Menu ref={menuRef} id={props.id} onSelect={onSelect}>
      <MenuContent>
        <MenuList>
          {props.options.map((item) => {
            return (
              props?.idKey !== undefined &&
              props?.valueKey !== undefined && (
                <MenuItem key={item?.[props.idKey]} itemId={item[props.idKey]}>
                  {item[props.valueKey]}
                </MenuItem>
              )
            );
          })}
        </MenuList>
      </MenuContent>
    </Menu>
  );

  const menuToggle = (
    <MenuToggle
      disabled={props.disabled}
      ref={toggleRef}
      onClick={toggleClick}
      isExpanded={isOpen}
      icon={props?.icon && props.icon}
      style={props?.style}
    >
      {value && value}
    </MenuToggle>
  );

  const select = (
    <div ref={containerRefDropdown}>
      <Popper
        trigger={menuToggle}
        triggerRef={toggleRef}
        popper={menu}
        popperRef={menuRef}
        appendTo={containerRefDropdown.current || undefined}
        isVisible={isOpen}
      />
    </div>
  );

  return <React.Fragment>{select}</React.Fragment>;
};
