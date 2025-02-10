import { TextInputType } from "@app/Types/TextInputTypes";
import { TextInput } from "@patternfly/react-core";
import React, { useEffect, useRef, useState } from "react";

export const CustomInput: React.FunctionComponent<TextInputType> = (props) => {
  const [localeValue, setLocaleValue] = useState<string | number | null | undefined>(props.value);
  const initialValueRef = useRef<string | number | null | undefined>(props.value);

  useEffect(() => {
    return setLocaleValue(props.value);
  }, [props.value])

  const handleBlur = (event: React.FocusEvent<HTMLInputElement>) => {
    const value = event.target.value;

    if (value !== String(initialValueRef.current)) {
      props.onBlur(value);
    }
  }

  const handleFocus = () => {
    initialValueRef.current = localeValue;
  }

  return (
    <>
      <TextInput
        id={props.id}
        value={localeValue || ""}
        type={props.type || "text"}
        onBlur={handleBlur}
        onChange={(_event, value) => setLocaleValue(value)}
        onFocus={handleFocus}
        placeholder={props.placeholder}
        aria-label={props.id}
        style={{textAlign: props.type === 'number' ? 'right' : 'left'}}
      />
    </>
  )
}
