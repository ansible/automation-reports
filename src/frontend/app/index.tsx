import * as React from 'react';
import '@patternfly/react-core/dist/styles/base.css';
import { BrowserRouter as Router } from 'react-router-dom';
import { AppLayout } from '@app/AppLayout';
import { AppRoutes } from '@app/routes';
import '@app/styles/app.scss';
import { ToasterProvider } from '@app/Components';

const App: React.FunctionComponent = () => (
  <Router>
    <AppLayout>
      <ToasterProvider>
      <AppRoutes />
      </ToasterProvider>
    </AppLayout>
  </Router>
);

export default App;
