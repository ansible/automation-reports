import axios from 'axios';

let apiUrl = process.env.API_URL;

if (!apiUrl) {
  throw new Error('Missing API url');
}

apiUrl = apiUrl.replace(/\/$|$/, '/');

const client = axios.create({
  baseURL: apiUrl,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default client;
