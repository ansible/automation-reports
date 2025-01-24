import api from '../client/apiClient';

const fetchTemplateOptions = async () => {
  return api.get('api/v1/template_options/');
};

export const RestService = {
  fetchTemplateOptions: fetchTemplateOptions,
};
