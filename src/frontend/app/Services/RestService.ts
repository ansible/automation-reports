import api from '../client/apiClient';
import { ReportDetail, TableResponse, UrlParams } from '@app/Types';

const buildQueryString = (params: object): string => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  });
  return query.toString() ? `?${query.toString()}` : '';
};

const fetchTemplateOptions = async () => {
  return api.get('api/v1/template_options/');
};

const fetchReports = async (params: UrlParams): Promise<TableResponse> => {
  const queryString = buildQueryString(params);
  return api.get(`api/v1/report/${queryString}`).then((response) => response.data);
};

const fetchReportDetails = async (params: UrlParams): Promise<ReportDetail> => {
  const queryString = buildQueryString(params);
  return api.get(`api/v1/report/details/${queryString}`).then((response) => response.data);
};

const updateCosts = async (payload) => {
  return api.post('api/v1/costs/', payload);
};

const updateTemplate = async (template_id: number, manualTimeMinutes: number) => {
  return api.put(`api/v1/templates/${template_id}/`, { manual_time_minutes: manualTimeMinutes });
};

export const RestService = {
  fetchTemplateOptions: fetchTemplateOptions,
  fetchReports: fetchReports,
  fetchReportDetails: fetchReportDetails,
  updateCosts: updateCosts,
  buildQueryString: buildQueryString,
  updateTemplate: updateTemplate,
};
