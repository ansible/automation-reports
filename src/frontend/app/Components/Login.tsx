import React, { useEffect, useRef, useState } from 'react';
import {
  ActionGroup,
  Alert,
  Button,
  Form,
  FormGroup,
  LoginPage,
  Spinner,
  TextInput,
} from '@patternfly/react-core';
import { useAuthStore } from '@app/Store/authStore';
import { useLocation, useNavigate } from 'react-router-dom';
import { useSearchParams } from 'react-router-dom';
import { AppSettings } from '@app/Types/AuthTypes';
import api from '@app/client/apiClient';
import logo from '../../assets/images/logo.svg';


export const Login: React.FunctionComponent = () => {
  const [loading, setLoading] = useState(false);
  const [searchParams] = useSearchParams();
  const fetchAppSettings = useAuthStore((state) => state.fetchAppSettings);
  const authorizeUser = useAuthStore((state) => state.authorizeUser);
  const getMyUserData = useAuthStore((state) => state.getMyUserData);
  const appSettings: AppSettings | null = useAuthStore((state) => state.appSettings);
  const error = useAuthStore((state) => state.error);
  const hasFetched = useRef(false);
  const initialized = useRef(false);
  const location = useLocation();
  const navigate = useNavigate();

  // Dev login form state (shown when AAP settings fail to load)
  const [devMode, setDevMode] = useState(false);
  const [devUsername, setDevUsername] = useState('');
  const [devPassword, setDevPassword] = useState('');
  const [devError, setDevError] = useState<string | null>(null);
  const [devLoading, setDevLoading] = useState(false);

  const defaultErrorMessage = 'Something went wrong during authorization. Please contact your system administrator.';
  const [errorMessage, seterrorMessage] = useState('false');

  const loginWithAAP = () => {
    window.location.href = `${appSettings?.url}?client_id=${appSettings?.client_id}&response_type=${appSettings?.response_type}&approval_prompt=${appSettings?.approval_prompt}`;
  };

  const handleLogin = (code: string) => {
    authorizeUser(code).then(() => {
      navigate('/');
    }).catch((e) => {
      seterrorMessage((
        e?.message ? e.message + ' Please contact your system administrator.' : defaultErrorMessage));
    }).finally(() => {
      setLoading(false);
    });
  };

  const handleDevLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setDevLoading(true);
    setDevError(null);
    try {
      await api.post('/api/v1/aap_auth/dev_login/', { username: devUsername, password: devPassword });
      await getMyUserData();
      navigate('/');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error ?? 'Login failed';
      setDevError(msg);
    } finally {
      setDevLoading(false);
    }
  };

  useEffect(() => {
    if (!hasFetched.current) {
      fetchAppSettings()
        .then(() => {
          // If settings loaded but url/client_id are blank, AAP isn't configured
          const s = useAuthStore.getState().appSettings;
          if (!s?.url || !s?.client_id) {
            setDevMode(true);
          }
        })
        .catch(() => {
          setDevMode(true);  // AAP not configured or unreachable
        });
      hasFetched.current = true;
    }

    if (location.pathname === '/auth-callback' && !initialized.current) {
      setLoading(true);
      const code = searchParams.get('code');
      if (code) {
        handleLogin(code);
      } else {
        setLoading(false);
        seterrorMessage('Authorization code is missing');
      }
      initialized.current = true;
    }
  }, []);

  // Dev/local login form — shown when AAP OAuth isn't configured
  if (devMode) {
    return (
      <LoginPage
        brandImgSrc={logo}
        brandImgAlt="Ansible Automation Platform"
        loginTitle="Sign in to your account"
        loginSubtitle="AAP OAuth is not configured — signing in with a local account"
      >
        {devError && (
          <Alert variant="danger" title={devError} isInline style={{ marginBottom: '16px' }} />
        )}
        <Form onSubmit={handleDevLogin}>
          <FormGroup label="Username" fieldId="dev-username" isRequired>
            <TextInput
              id="dev-username"
              value={devUsername}
              onChange={(_e, v) => setDevUsername(v)}
              isRequired
              autoComplete="username"
              autoFocus
            />
          </FormGroup>
          <FormGroup label="Password" fieldId="dev-password" isRequired>
            <TextInput
              id="dev-password"
              type="password"
              value={devPassword}
              onChange={(_e, v) => setDevPassword(v)}
              isRequired
              autoComplete="current-password"
            />
          </FormGroup>
          <ActionGroup>
            <Button
              variant="primary"
              type="submit"
              isDisabled={devLoading || !devUsername || !devPassword}
              isBlock
            >
              {devLoading ? <><Spinner size="sm" />&nbsp;Signing in…</> : 'Sign in'}
            </Button>
          </ActionGroup>
        </Form>
      </LoginPage>
    );
  }

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
            onClick={loginWithAAP}
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
