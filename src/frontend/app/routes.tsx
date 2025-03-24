import * as React from 'react';
import { Route, Routes } from 'react-router-dom';
import { Dashboard } from '@app/Dashboard';

export interface IAppRoute {
  label?: string; // Excluding the label will exclude the route from the nav sidebar in AppLayout
  /* eslint-disable @typescript-eslint/no-explicit-any */
  element: React.ReactElement;
  /* eslint-enable @typescript-eslint/no-explicit-any */
  exact?: boolean;
  path: string;
  title: string;
  routes?: undefined;
}

export interface IAppRouteGroup {
  label: string;
  routes: IAppRoute[];
}

const routes: IAppRoute[] = [
  {
    element: <Dashboard />,
    exact: true,
    label: 'Dashboard',
    path: '/',
    title: 'PatternFly Seed | Main Dashboard',
  },
];

const AppRoutes = (): React.ReactElement => (
  <Routes>
    {routes.map((route: IAppRoute, index: number) => (
      <Route path={route.path} element={route.element} key={index} />
    ))}
    <Route path="*" element={<Dashboard />} />
  </Routes>
);

export { AppRoutes, routes };
