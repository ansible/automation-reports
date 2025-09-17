import axios from 'axios';

let apiUrl = import.meta.env.VITE_API_URL;

if (!apiUrl) {
  throw new Error('Missing API url. Please set the VITE_API_URL environment variable.');
}

apiUrl = apiUrl.replace(/\/$|$/, '/');

const client = axios.create({
  baseURL: apiUrl,
  timeout: 40000,
  withCredentials: true,
  withXSRFToken: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-XSRF-TOKEN',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default client;
