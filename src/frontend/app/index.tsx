import * as React from 'react';
import '@patternfly/react-core/dist/styles/base.css';
import { BrowserRouter as Router } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import { AppLayout } from '@app/AppLayout';
import { AppRoutes } from '@app/routes';
import '@app/styles/app.scss';
import { ToasterProvider } from '@app/Components';
// Import i18n config BEFORE React render (CRITICAL)
import i18n from '@app/i18n/config';

const App: React.FunctionComponent = () => (
  <I18nextProvider i18n={i18n}>
    <Router>
      <React.Suspense fallback={<div>Loading...</div>}>
        <AppLayout>
          <ToasterProvider>
            <AppRoutes />
          </ToasterProvider>
        </AppLayout>
      </React.Suspense>
    </Router>
  </I18nextProvider>
);

export default App;
