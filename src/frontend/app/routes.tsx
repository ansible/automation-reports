import * as React from 'react';
import { Route, Routes, Navigate } from 'react-router-dom';
import { Dashboard } from '@app/Dashboard';
import { Login } from '@app/Components';
import { useAuthStore } from '@app/Store/authStore';
export interface IAppRoute {
  label?: string; // Excluding the label will exclude the route from the nav sidebar in AppLayout
  element: React.ReactElement;
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
    element: <Login />,
    exact: true,
    label: 'Login',
    path: '/login',
    title: 'login',
  },
  {
    element: <Login />,
    exact: true,
    label: 'Login',
    path: '/auth-callback',
    title: 'login',
  },
  {
    element: <Dashboard />,
    exact: true,
    label: 'Dashboard',
    path: '/',
    title: 'PatternFly Seed | Main Dashboard',
  },
];


const AppRoutes = (): React.ReactElement => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  return (
    <Routes>
      {routes.map((route: IAppRoute, index: number) => (
        <Route
          path={route.path} 
          element={
            isAuthenticated ? (
              route.path === '/login' || route.path === '/auth-callback' ? (
                <Navigate to="/" replace />
              ) : (
                route.element
              )
            ) : (
              route.path === '/' ? <Navigate to="/login" replace /> : route.element
            )
          }
          key={index} 
        />
      ))}
      <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />} />
    </Routes>
  ) 
};

export { AppRoutes, routes };
