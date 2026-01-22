import * as React from 'react';
import { Alert, AlertActionCloseButton, AlertGroup, AlertProps } from '@patternfly/react-core';
import { useContext, createContext, ReactNode, useState } from 'react';

export interface InterfaceToaster {
  add: (alert: AlertProps) => void;
  remove: (alert: AlertProps) => void;
}

export const ToasterContext = createContext<InterfaceToaster>({
  add: () => null,
  remove: () => null,
});

export function useToaster(): InterfaceToaster {
  return useContext(ToasterContext);
}

export function ToasterProvider(props: { children: ReactNode }) {
  const [alerts, setAlerts] = useState<AlertProps[]>([]);
  const [pageToaster] = useState<InterfaceToaster>(() => {
    function add(alert: AlertProps) {
      if (Number.isInteger(alert.timeout)) {
        setTimeout(() => remove(alert), alert.timeout as number);
        delete alert.timeout;
      }
      setAlerts((alerts) => {
        const alertIndex = alerts.findIndex((a) => a === alert);
        if (alertIndex !== -1) {
          const newAlerts = [...alerts];
          newAlerts[alertIndex] = alert;
          return newAlerts;
        } else {
          return [...alerts, alert];
        }
      });
    }
    function remove(alert: AlertProps) {
      setAlerts((alerts) => alerts.filter((a) => a !== alert));
    }
    return { add, remove };
  });

  return (
    <ToasterContext.Provider value={pageToaster}>
      <AlertGroup data-cy="alert-toaster" isToast isLiveRegion hasAnimations style={{ top: '6rem', }}>
        {alerts.map((alertProps, index) => (
          <Alert
            {...alertProps}
            key={alertProps.key ?? alertProps.id ?? index}
            actionClose={<AlertActionCloseButton onClose={() => pageToaster.remove(alertProps)} />}
          />
        ))}
      </AlertGroup>
      {props.children}
    </ToasterContext.Provider>
  );
}

export function toasterErrorMsg(msg: string, timeOut?: number): AlertProps {
  return {
    variant: 'danger',
    title: msg,
    timeout: timeOut ? timeOut : 3000,
  };
}

export function toasterFromError(err: unknown): AlertProps {
  const msg = (err as { message?: string })?.message ?? 'Something went wrong. Please try again later.';
  return toasterErrorMsg(msg);
}

export function toasterSuccessMsg(msg: string, timeOut?: number): AlertProps {
  return {
    variant: 'success',
    title: msg,
    timeout: timeOut ? timeOut : 3000,
  };
}
