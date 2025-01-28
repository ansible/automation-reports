import * as React from 'react';
import { Badge, Menu, MenuContent, MenuItem, MenuList, MenuToggle, Popper } from '@patternfly/react-core';
import { MultiChoiceDropdownProps, baseDropDownDefaultProps } from '@app/Types';

export const MultiChoiceDropdown: React.FunctionComponent<MultiChoiceDropdownProps> = (
  props: MultiChoiceDropdownProps,
) => {
  props = { ...baseDropDownDefaultProps, ...props };
  const selectContainerRef = React.useRef<HTMLDivElement>(null);
  const toggleRef = React.useRef<HTMLButtonElement>(null);
  const menuRef = React.useRef<HTMLDivElement>(null);
  const [isMenuOpen, setIsMenuOpen] = React.useState<boolean>(false);

  const handleMenuClickOutside = (event: MouseEvent) => {
    if (isMenuOpen && !menuRef.current?.contains(event.target as Node)) {
      setIsMenuOpen(false);
    }
  };

  React.useEffect(() => {
    window.addEventListener('click', handleMenuClickOutside);
    return () => {
      window.removeEventListener('click', handleMenuClickOutside);
    };
  }, [isMenuOpen, menuRef]);

  const onToggleClick = (ev: React.MouseEvent) => {
    ev.stopPropagation();
    setIsMenuOpen(!isMenuOpen);
  };

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
    <Menu
      ref={menuRef}
      id="mixed-group-items-menu"
      onSelect={props.onSelect}
      style={
        {
          width: '220px',
        } as React.CSSProperties
      }
    >
      {props?.options?.length && (
        <MenuContent>
          <MenuList>
            {props.options.map((item: object) => {
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
