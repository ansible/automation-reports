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
  TextInput,
  Title,
} from '@patternfly/react-core';
import useSetupStore from '@app/Store/setupStore';

interface StepInfraProps {
  onNext: () => void;
  onBack: () => void;
}

const StepInfra: React.FC<StepInfraProps> = ({ onNext, onBack }) => {
  const infra = useSetupStore((s) => s.infra);
  const setInfra = useSetupStore((s) => s.setInfra);

  return (
    <div>
      <Title headingLevel="h2" size="lg" style={{ marginBottom: '8px' }}>
        Infrastructure Settings
      </Title>
      <Alert
        variant="info"
        isInline
        title="Only needed for inventory file download"
        style={{ marginBottom: '16px' }}
      >
        These fields are used to generate a pre-filled <code>inventory</code> file for the Ansible installer.
        They do not affect the currently running application.
      </Alert>

      <Form style={{ maxWidth: '560px' }}>
        <FormGroup label="Dashboard Host" fieldId="infra-dashboard-host">
          <TextInput
            id="infra-dashboard-host"
            value={infra.dashboard_host}
            onChange={(_e, v) => setInfra({ dashboard_host: v })}
            placeholder="dashboard.example.com"
          />
          <FormHelperText>
            <HelperText>
              <HelperTextItem>The hostname where the dashboard will be installed</HelperTextItem>
            </HelperText>
          </FormHelperText>
        </FormGroup>

        <FormGroup label="Database Host" fieldId="infra-db-host">
          <TextInput
            id="infra-db-host"
            value={infra.db_host}
            onChange={(_e, v) => setInfra({ db_host: v })}
            placeholder="192.168.1.10"
          />
          <FormHelperText>
            <HelperText>
              <HelperTextItem>Must be an IP address or hostname (not localhost or 127.0.0.1)</HelperTextItem>
            </HelperText>
          </FormHelperText>
        </FormGroup>

        <FormGroup label="Database Username" fieldId="infra-db-username">
          <TextInput
            id="infra-db-username"
            value={infra.db_username}
            onChange={(_e, v) => setInfra({ db_username: v })}
          />
        </FormGroup>

        <FormGroup label="Database Password" fieldId="infra-db-password">
          <TextInput
            id="infra-db-password"
            type="password"
            value={infra.db_password}
            onChange={(_e, v) => setInfra({ db_password: v })}
          />
        </FormGroup>

        <FormGroup label="Database Name" fieldId="infra-db-name">
          <TextInput
            id="infra-db-name"
            value={infra.db_name}
            onChange={(_e, v) => setInfra({ db_name: v })}
          />
        </FormGroup>

        <FormGroup label="PostgreSQL Admin Username" fieldId="infra-db-admin-username">
          <TextInput
            id="infra-db-admin-username"
            value={infra.db_admin_username}
            onChange={(_e, v) => setInfra({ db_admin_username: v })}
          />
        </FormGroup>

        <FormGroup label="PostgreSQL Admin Password" fieldId="infra-db-admin-password">
          <TextInput
            id="infra-db-admin-password"
            type="password"
            value={infra.db_admin_password}
            onChange={(_e, v) => setInfra({ db_admin_password: v })}
          />
        </FormGroup>

        <FormGroup label="Dashboard Admin Password" fieldId="infra-dashboard-admin-password">
          <TextInput
            id="infra-dashboard-admin-password"
            type="password"
            value={infra.dashboard_admin_password}
            onChange={(_e, v) => setInfra({ dashboard_admin_password: v })}
          />
        </FormGroup>

        <FormGroup label="HTTP Port" fieldId="infra-http-port">
          <TextInput
            id="infra-http-port"
            type="number"
            value={String(infra.nginx_http_port)}
            onChange={(_e, v) => setInfra({ nginx_http_port: parseInt(v, 10) || 8083 })}
            style={{ maxWidth: '120px' }}
          />
        </FormGroup>

        <FormGroup label="HTTPS Port" fieldId="infra-https-port">
          <TextInput
            id="infra-https-port"
            type="number"
            value={String(infra.nginx_https_port)}
            onChange={(_e, v) => setInfra({ nginx_https_port: parseInt(v, 10) || 8447 })}
            style={{ maxWidth: '120px' }}
          />
        </FormGroup>

        <FormGroup label="TLS Certificate Path" fieldId="infra-tls-cert">
          <TextInput
            id="infra-tls-cert"
            value={infra.dashboard_tls_cert}
            onChange={(_e, v) => setInfra({ dashboard_tls_cert: v })}
            placeholder="/path/to/dashboard.crt (optional)"
          />
        </FormGroup>

        <FormGroup label="TLS Key Path" fieldId="infra-tls-key">
          <TextInput
            id="infra-tls-key"
            value={infra.dashboard_tls_key}
            onChange={(_e, v) => setInfra({ dashboard_tls_key: v })}
            placeholder="/path/to/dashboard.key (optional)"
          />
        </FormGroup>

        <ActionGroup>
          <Button variant="primary" onClick={onNext}>
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

export default StepInfra;
