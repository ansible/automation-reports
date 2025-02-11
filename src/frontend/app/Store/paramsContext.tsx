import React, { createContext, useState } from 'react';
import { UrlParams } from '@app/Types';

export interface ParamsContextType {
  params: UrlParams;
  setParams: React.Dispatch<React.SetStateAction<UrlParams>>;
}

export const ParamsContext = createContext<ParamsContextType | undefined>(undefined as any);

const ParamsContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [params, setParams] = useState<UrlParams>({
    page: 1,
    page_size: 10,
    organization: null,
    date_range: null,
    start_date: null,
    end_date: null,
    label: null,
    job_template: null,
    ordering: null,
  });

  return <ParamsContext.Provider value={{ params, setParams }}>{children}</ParamsContext.Provider>;
};

export default ParamsContextProvider;
