import React, { createContext, useState } from "react";

export interface ParamsType {
  page: number;
  page_size: number;
  organization: number[] | null;
  date_range: string | null;
  start_date: string | null;
  end_date: string | null;
  label: number[] | null;
  job_template: number[] | null;
  ordering: string | null;
}

export interface ParamsContextType {
  params: ParamsType;
  setParams: React.Dispatch<React.SetStateAction<ParamsType>>
}

export const ParamsContext = createContext<ParamsContextType | undefined>(undefined as any);

const ParamsContextProvider: React.FC<{children: React.ReactNode}> = ({children}) => {
  const [params, setParams] = useState<ParamsType>({
    page: 1,
    page_size: 10,
    organization: null,
    date_range: null,
    start_date: null,
    end_date: null,
    label: null,
    job_template: null,
    ordering: null
  });

  return (
    <ParamsContext.Provider value={{params, setParams}}>
      {children}
    </ParamsContext.Provider>
  )
}

export default ParamsContextProvider;