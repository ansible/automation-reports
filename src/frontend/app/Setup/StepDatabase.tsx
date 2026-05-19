import * as React from 'react';
import {
  ActionGroup,
  Alert,
  Button,
  Form,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem,
  Spinner,
  TextInput,
  Title,
} from '@patternfly/react-core';
import api from '@app/client/apiClient';
import useSetupStore from '@app/Store/setupStore';

interface StepDatabaseProps {
  onNext: () => void;
  onBack: () => void;
}

const StepDatabase: React.FC<StepDatabaseProps> = ({ onNext, onBack }) => {
  const cluster = useSetupStore((s) => s.cluster);
  const setCluster = useSetupStore((s) => s.setCluster);

  const [testing, setTesting] = React.useState(false);
  const [testResult, setTestResult] = React.useState<'idle' | 'success' | 'failed'>('idle');
  const [testError, setTestError] = React.useState<string | null>(null);

  // Pre-fill db_host from cluster address if blank
  React.useEffect(() => {
    if (!cluster.db_host && cluster.address) {
      setCluster({ db_host: cluster.address });
    }
  }, []);

  const isValid =
    cluster.db_host.trim() !== '' &&
    cluster.db_user.trim() !== '' &&
    cluster.db_password.trim() !== '' &&
    cluster.db_name.trim() !== '';

  const handleTest = async () => {
    setTesting(true);
    setTestResult('idle');
    setTestError(null);
    try {
      const res = await api.post<{ success: boolean; error: string | null }>('/api/v1/setup/test_connection/', {
        sync_mode: 'database',
        db_host: cluster.db_host,
        db_port: cluster.db_port,
        db_name: cluster.db_name,
        db_user: cluster.db_user,
        db_password: cluster.db_password,
      });
      setTestResult(res.data.success ? 'success' : 'failed');
      setTestError(res.data.error);
    } catch {
      setTestResult('failed');
      setTestError('Database connection test failed');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div>
      <Title headingLevel="h2" size="lg" style={{ marginBottom: '16px' }}>
        Database Connection
      </Title>
      <p style={{ marginBottom: '16px' }}>
        Provide read-only credentials for AAP&apos;s PostgreSQL database.
      </p>

      <Alert
        variant="info"
        title="Read-only database account required"
        isInline
        style={{ marginBottom: '24px' }}
      >
        Create a read-only PostgreSQL user in AAP&apos;s database. The user needs SELECT permission on AAP tables.
        Example: <code>GRANT SELECT ON ALL TABLES IN SCHEMA public TO &lt;user&gt;;</code>
      </Alert>

      <Form style={{ maxWidth: '560px' }}>
        <FormGroup label="DB Host" fieldId="db-host" isRequired>
          <TextInput
            id="db-host"
            value={cluster.db_host}
            onChange={(_e, v) => setCluster({ db_host: v.replace(/^https?:\/\//i, '') })}
            placeholder="44.201.211.61"
            isRequired
          />
          <FormHelperText>
            <HelperText>
              <HelperTextItem>IP address or hostname only — do not include <code>http://</code> or <code>https://</code></HelperTextItem>
            </HelperText>
          </FormHelperText>
        </FormGroup>

        <FormGroup label="DB Port" fieldId="db-port" isRequired>
          <TextInput
            id="db-port"
            type="number"
            value={String(cluster.db_port)}
            onChange={(_e, v) => setCluster({ db_port: parseInt(v, 10) || 5432 })}
            isRequired
          />
        </FormGroup>

        <FormGroup label="Database Name" fieldId="db-name" isRequired>
          <TextInput
            id="db-name"
            value={cluster.db_name}
            onChange={(_e, v) => setCluster({ db_name: v })}
            placeholder="awx"
            isRequired
          />
        </FormGroup>

        <FormGroup label="DB User" fieldId="db-user" isRequired>
          <TextInput
            id="db-user"
            value={cluster.db_user}
            onChange={(_e, v) => setCluster({ db_user: v })}
            isRequired
          />
        </FormGroup>

        <FormGroup label="DB Password" fieldId="db-password" isRequired>
          <TextInput
            id="db-password"
            type="password"
            value={cluster.db_password}
            onChange={(_e, v) => setCluster({ db_password: v })}
            isRequired
          />
        </FormGroup>

        {testError && testResult === 'failed' && (
          <Alert variant="danger" title={testError} isInline />
        )}
        {testResult === 'success' && (
          <Alert variant="success" title="Database connection successful" isInline />
        )}

        <ActionGroup>
          <Button
            variant="secondary"
            onClick={handleTest}
            isDisabled={!isValid || testing}
          >
            {testing ? <><Spinner size="sm" /> Testing...</> : 'Test Connection'}
          </Button>
        </ActionGroup>

        <ActionGroup>
          <Button variant="primary" onClick={onNext} isDisabled={!isValid}>
            Next
          </Button>
          <Button variant="link" onClick={onBack}>
            Back
          </Button>
        </ActionGroup>
      </Form>
    </div>
  );
};

export default StepDatabase;
