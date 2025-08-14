import React, { useEffect, useRef, useState } from 'react';
import { Alert, Button, LoginPage, Spinner } from '@patternfly/react-core';
import { useAuthStore } from '@app/Store/authStore';
import { useLocation, useNavigate } from 'react-router-dom';
import { useSearchParams } from 'react-router-dom';
import { AppSettings } from '@app/Types/AuthTypes';
import logo from '../../assets/images/logo.svg'

export const Login: React.FunctionComponent = () => {
  const [loading, setLoading] = useState(false);
  const [searchParams] = useSearchParams();
  const fetchAppSettings = useAuthStore((state) => state.fetchAppSettings);
  const authorizeUser = useAuthStore((state) => state.authorizeUser);
  const appSettings: AppSettings | null = useAuthStore((state) => state.appSettings);
  const error = useAuthStore((state) => state.error);
  const hasFetched = useRef(false);
  const initialized = useRef(false);
  const location = useLocation();
  const navigate = useNavigate();
  const errorMessage = "Something went wrong during authorization. Please contact your system administrator.";

  const loginWithAAp = () => {
    const baseUrl = 'https://10.44.17.180';
    window.location.href = `${baseUrl}/o/authorize?client_id=${appSettings?.client_id}&response_type=${appSettings?.response_type}&approval_prompt=${appSettings?.approval_prompt}`;
  }

  useEffect(() => {
    if (!hasFetched.current) {
      fetchAppSettings();
      hasFetched.current = true;
    }

    if (location.pathname === '/auth-callback' && !initialized.current) {
      setLoading(true);
      const code = searchParams.get('code');
      if (code) {
        authorizeUser(code)
          .then(() => setLoading(false))
          .catch(() => {
            setLoading(false);
            navigate('/login');
          });
      } else {
        setLoading(false);
        console.error('Authorization code is missing');
      }
      initialized.current = true;
    }
  }, []);

  return (
    <>
      <LoginPage
        brandImgSrc={logo}
        brandImgAlt="Logo"
        loginTitle="Log in to your account"
      >
        {loading ? (
          <div className="pf-v6-l-flex pf-m-justify-content-center pf-v6-u-py-md">
            <Spinner className="spinner" aria-label="Loader" />
          </div>
        ) : error ? (
          <Alert variant="danger" isInline title={errorMessage} />
        ) : (
          <Button
            onClick={loginWithAAp}
            className="btn-pdf pf-v6-u-ml-auto-on-xl pf-v6-u-ml-0"
            variant="primary"
          >
            Login with {appSettings?.name}
          </Button>
        )}
      </LoginPage>
    </>
  );
};
