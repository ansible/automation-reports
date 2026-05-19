import * as React from 'react';
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
import logo from '../../assets/images/logo.svg';
import useSetupStore from '@app/Store/setupStore';

interface LocalLoginFormProps {
  onAuthenticated: () => void;
}

const LocalLoginForm: React.FC<LocalLoginFormProps> = ({ onAuthenticated }) => {
  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  const localLogin = useSetupStore((s) => s.localLogin);
  const localLoginError = useSetupStore((s) => s.localLoginError);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await localLogin(username, password);
      onAuthenticated();
    } catch {
      // error is set in store
    } finally {
      setLoading(false);
    }
  };

  return (
    <LoginPage
      brandImgSrc={logo}
      brandImgAlt="Ansible Automation Platform"
      loginTitle="Sign in to continue setup"
      loginSubtitle="Use your administrator account to configure the dashboard"
    >
      {localLoginError && (
        <Alert
          variant="danger"
          title={localLoginError}
          isInline
          style={{ marginBottom: '16px' }}
        />
      )}
      <Form onSubmit={handleSubmit}>
        <FormGroup label="Username" fieldId="setup-username" isRequired>
          <TextInput
            id="setup-username"
            value={username}
            onChange={(_e, v) => setUsername(v)}
            isRequired
            autoComplete="username"
            autoFocus
          />
        </FormGroup>
        <FormGroup label="Password" fieldId="setup-password" isRequired>
          <TextInput
            id="setup-password"
            type="password"
            value={password}
            onChange={(_e, v) => setPassword(v)}
            isRequired
            autoComplete="current-password"
          />
        </FormGroup>
        <ActionGroup>
          <Button
            variant="primary"
            type="submit"
            isDisabled={loading || !username || !password}
            isBlock
          >
            {loading ? (
              <>
                <Spinner size="sm" aria-label="Signing in" />
                &nbsp; Signing in…
              </>
            ) : (
              'Sign in'
            )}
          </Button>
        </ActionGroup>
      </Form>
    </LoginPage>
  );
};

export default LocalLoginForm;
