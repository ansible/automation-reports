import api from '../client/apiClient';
import {
  FilterOptionWithId,
  FilterSet, OptionsResponse,
  OrderingParams,
  ReportDetail,
  RequestFilter,
  TableResponse,
  TableResult,
  UrlParams
} from '@app/Types';
import { getErrorMessage } from '@app/Utils';

const downloadAttachment = (data: never, name: string) => {
  const url = window.URL.createObjectURL(new Blob([data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', name);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const buildQueryString = (params: object): string => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  });
  return query.toString() ? `?${query.toString()}` : '';
};

const fetchAapSettings = async () => {
  return api.get('/api/v1/aap_auth/settings/');
};

const authorizeUser = async (authCode: string, callback_uri: string) => {
  return api
    .post('/api/v1/aap_auth/token/', {
      auth_code: authCode,
      redirect_uri: callback_uri
    })
    .then((response) => response.data);
};

const logoutUser = async () => {
  return api
    .post('/api/v1/aap_auth/logout/')
    .then((response) => response.data);
};

const refreshAccessToken = async () => {
  return api
    .post('/api/v1/aap_auth/refresh_token/', {})
    .then((response) => response.data);
};

const getMyUserData = async () => {
  return api.get('/api/v1/users/me/').then((response) => response.data);
};

const fetchTemplateOptions = async () => {
  return api.get('api/v1/template_options/');
};

const fetchReports = async (signal: AbortSignal, params: UrlParams): Promise<TableResponse> => {
  const queryString = buildQueryString(params);
  return api
    .get(`api/v1/report/${queryString}`, {
      signal: signal
    })
    .then((response) => response.data);
};

const fetchReportDetails = async (signal: AbortSignal, params: RequestFilter): Promise<ReportDetail> => {
  const queryString = buildQueryString(params);
  return api
    .get(`api/v1/report/details/${queryString}`, {
      signal: signal
    })
    .then((response) => response.data);
};

const exportToCSV = async (params: RequestFilter & OrderingParams): Promise<void> => {
  const queryString = buildQueryString(params);
  return api
    .get(`api/v1/report/csv/${queryString}`, {
      headers: {
        'Content-Type': 'text/csv; charset=utf-8'
      }
    })
    .then((response) => {
      downloadAttachment(response.data as never, 'AAP_Automation_Dashboard_Report.csv');
      Promise.resolve();
    })
};

const exportToPDF = async (
  params: RequestFilter & OrderingParams,
  jobChart: string | null,
  hostChart: string | null
): Promise<void> => {
  const queryString = buildQueryString(params);
  return api
    .post(`api/v1/report/pdf/${queryString}`,
      {
        job_chart: jobChart,
        host_chart: hostChart
      },
      {
        responseType: 'blob',
        timeout: 0
      })
    .then((response) => {
      downloadAttachment(response.data as never, 'AAP_Automation_Dashboard_Report.pdf');
      Promise.resolve();
    })
};

const updateCosts = async (payload) => {
  return api.post('api/v1/costs/', payload);
};

const updateTemplate = async (item: TableResult) => {
  return api.put(`api/v1/templates/${item.job_template_id}/`, {
    time_taken_manually_execute_minutes: item.time_taken_manually_execute_minutes,
    time_taken_create_automation_minutes: item.time_taken_create_automation_minutes
  });
};

const setCurrency = async (currencyId: number) => {
  return api.post('api/v1/common/settings/', { type: 'currency', value: currencyId });
};

const saveEnableTemplateCreationTime = async (value: boolean) => {
  return api.post('api/v1/common/settings/', { type: 'enable_template_creation_time', value: value });
};

const saveView = async (viewData: FilterSet): Promise<FilterSet> => {
  if (viewData.id) {
    return api.put(`api/v1/common/filter_set/${viewData.id}/`, viewData).then((response) => response.data);
  }
  return api.post('api/v1/common/filter_set/', viewData).then((response) => response.data);
};

const deleteView = async (viewId: number) => {
  return api.delete(`api/v1/common/filter_set/${viewId}/`);
};

const resetUserInputsToDefaults = async ()=>{
  return api.post('api/v1/template_options/restore_user_inputs/', {})
}

const fetchFilterOptions: (endPoint: string, params: object) => Promise<OptionsResponse> = async (endPoint: string, params: object): Promise<OptionsResponse> => {
  const queryString = buildQueryString(params);
  return api
    .get(`${endPoint}${queryString}`, {})
    .then((response) => response.data);
};
const fetchFilterOption: (endPoint: string, id: number) => Promise<FilterOptionWithId> = async (endPoint: string, id: number): Promise<FilterOptionWithId> => {
  return api
    .get(`${endPoint}${id}/`, {})
    .then((response) => response.data);
};

export const RestService = {
  fetchAapSettings: fetchAapSettings,
  authorizeUser: authorizeUser,
  getMyUserData: getMyUserData,
  refreshAccessToken: refreshAccessToken,
  fetchTemplateOptions: fetchTemplateOptions,
  fetchReports: fetchReports,
  fetchReportDetails: fetchReportDetails,
  updateCosts: updateCosts,
  buildQueryString: buildQueryString,
  updateTemplate: updateTemplate,
  setCurrency: setCurrency,
  saveView: saveView,
  deleteView: deleteView,
  exportToCSV: exportToCSV,
  exportToPDF: exportToPDF,
  saveEnableTemplateCreationTime: saveEnableTemplateCreationTime,
  logoutUser: logoutUser,
  fetchFilterOptions: fetchFilterOptions,
  fetchFilterOption: fetchFilterOption,
  resetUserInputsToDefaults: resetUserInputsToDefaults,
};
