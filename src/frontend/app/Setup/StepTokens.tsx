import * as React from 'react';
import {
  ActionGroup,
  Alert,
  Button,
  ExpandableSection,
  Form,
  FormGroup,
  TextInput,
  Title,
} from '@patternfly/react-core';
import useSetupStore from '@app/Store/setupStore';

interface StepTokensProps {
  onNext: () => void;
  onBack: () => void;
}

const StepTokens: React.FC<StepTokensProps> = ({ onNext, onBack }) => {
  const cluster = useSetupStore((s) => s.cluster);
  const setCluster = useSetupStore((s) => s.setCluster);
  const testConnection = useSetupStore((s) => s.testConnection);
  const connectionTest = useSetupStore((s) => s.connectionTest);
  const connectionError = useSetupStore((s) => s.connectionError);

  const isValid = cluster.access_token.trim() !== '';

  const handleTest = async () => {
    await testConnection();
  };

  return (
    <div>
      <Title headingLevel="h2" size="lg" style={{ marginBottom: '16px' }}>
        OAuth Tokens
      </Title>
      <p style={{ marginBottom: '16px' }}>
        Enter the access and refresh tokens that allow the dashboard to read job data from AAP.
      </p>

      <ExpandableSection toggleText="How do I get these tokens?" style={{ marginBottom: '24px' }}>
        <ol style={{ paddingLeft: '20px', lineHeight: '1.8' }}>
          <li>
            In AAP Controller, go to <strong>Users → {'<your user>'} → Tokens</strong>
          </li>
          <li>
            Click <strong>Add</strong> and select the OAuth2 application you created earlier
          </li>
          <li>Set the scope to <strong>Read</strong></li>
          <li>
            After saving, copy both the <strong>Access Token</strong> and the <strong>Refresh Token</strong> shown
            — the refresh token is only displayed once
          </li>
        </ol>
      </ExpandableSection>

      <Form style={{ maxWidth: '560px' }}>
        <FormGroup label="Access Token" fieldId="token-access" isRequired>
          <TextInput
            id="token-access"
            type="password"
            value={cluster.access_token}
            onChange={(_e, v) => setCluster({ access_token: v })}
            isRequired
          />
        </FormGroup>

        <FormGroup label="Refresh Token" fieldId="token-refresh">
          <TextInput
            id="token-refresh"
            type="password"
            value={cluster.refresh_token}
            onChange={(_e, v) => setCluster({ refresh_token: v })}
            placeholder="Optional — enables automatic token renewal"
          />
        </FormGroup>

        {connectionError && (
          <Alert variant="danger" title={connectionError} isInline />
        )}
        {connectionTest === 'success' && (
          <Alert variant="success" title="Connection successful — tokens are valid" isInline />
        )}

        <ActionGroup>
          <Button
            variant="secondary"
            onClick={handleTest}
            isDisabled={!cluster.address || !cluster.access_token || connectionTest === 'testing'}
          >
            Test Connection
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

export default StepTokens;
