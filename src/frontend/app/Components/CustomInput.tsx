import { TextInputType } from '@app/Types/TextInputTypes';
import { HelperText, HelperTextItem, TextInput } from '@patternfly/react-core';
import React, { useEffect, useRef, useState } from 'react';
import { TimesIcon } from '@patternfly/react-icons/dist/esm/icons/times-icon';

export const CustomInput: React.FunctionComponent<TextInputType> = (props) => {
  const [localeValue, setLocaleValue] = useState<string | number | null | undefined>(props.value);
  const initialValueRef = useRef<string | number | null | undefined>(props.value);

  useEffect(() => {
    return setLocaleValue(props.value);
  }, [props.value]);

  const handleBlur = (event: React.FocusEvent<HTMLInputElement>) => {
    const value = event.target.value;
    props.onBlur(value);
  };

  const handleFocus = (ev?: never) => {
    initialValueRef.current = localeValue;
    if (props?.onFocus) {
      props?.onFocus(ev);
    }
  };

  return (
    <>
      <TextInput
        id={props.id}
        value={localeValue || ''}
        type={props.type || 'text'}
        onBlur={handleBlur}
        onChange={(_event, value) => setLocaleValue(value)}
        onFocus={handleFocus}
        placeholder={props.placeholder}
        aria-label={props.id}
        style={{ textAlign: props.type === 'number' ? 'right' : 'left' }}
        min={props.type === 'number' ? 0 : undefined}
        validated={props.errorMessage ? 'error' : undefined}
        isDisabled={props.isDisabled}
      />
      {props.errorMessage && (
        <HelperText>
          <HelperTextItem variant="error" icon={<TimesIcon />}>
            {props.errorMessage}
          </HelperTextItem>
        </HelperText>
      )}
    </>
  );
};
