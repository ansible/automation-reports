import api from '../client/apiClient';

const fetchTemplateOptions = async () => {
  return api.get('api/v1/template_options/');
};

const fetchReports = async (params) => {
  return api.get('api/v1/report/' + params);
}

const fetchReportDetails = async (params) => {
  return api.get('api/v1/report/details' + params);
} 

export const RestService = {
  fetchTemplateOptions: fetchTemplateOptions,
  fetchReports: fetchReports,
  fetchReportDetails: fetchReportDetails,
};
