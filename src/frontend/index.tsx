import React from 'react';
import ReactDOM from 'react-dom/client';
import App from '@app/index';
import { Provider } from 'react-redux';
import { store } from '@app/Store/store';

if (process.env.NODE_ENV !== 'production') {
  const config = {
    rules: [
      {
        id: 'color-contrast',
        enabled: false,
      },
    ],
  };
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const axe = require('react-axe');
  axe(React, ReactDOM, 1000, config).then();
}

const root = ReactDOM.createRoot(document.getElementById('app') as Element);

root.render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>,
);
