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
  Radio,
  Select,
  SelectList,
  SelectOption,
  Spinner,
  Switch,
  TextInput,
  Title,
} from '@patternfly/react-core';
import { MenuToggle, MenuToggleElement } from '@patternfly/react-core';
import useSetupStore from '@app/Store/setupStore';
import { AAPVersion } from '@app/Types/SetupTypes';

interface StepClusterProps {
  onNext: () => void;
  onBack: () => void;
}

const AAP_VERSIONS: AAPVersion[] = ['AAP 2.7', 'AAP 2.6', 'AAP 2.5', 'AAP 2.4'];

const StepCluster: React.FC<StepClusterProps> = ({ onNext, onBack }) => {
  const cluster = useSetupStore((s) => s.cluster);
  const setCluster = useSetupStore((s) => s.setCluster);
  const testConnection = useSetupStore((s) => s.testConnection);
  const connectionTest = useSetupStore((s) => s.connectionTest);
  const connectionError = useSetupStore((s) => s.connectionError);

  const [versionOpen, setVersionOpen] = React.useState(false);
  const [protocolOpen, setProtocolOpen] = React.useState(false);

  const syncMode = cluster.sync_mode ?? 'api';

  const isValid =
    cluster.address.trim() !== '' &&
    (syncMode === 'database' || (cluster.client_id.trim() !== '' && cluster.client_secret.trim() !== ''));

  const handleTest = async () => {
    await testConnection();
  };

  return (
    <div>
      <Title headingLevel="h2" size="lg" style={{ marginBottom: '16px' }}>
        AAP Cluster Connection
      </Title>
      <p style={{ marginBottom: '24px' }}>
        Enter the connection details for your Ansible Automation Platform Controller.
      </p>

      <Form style={{ maxWidth: '560px' }}>
        <FormGroup label="How will this cluster sync data?" fieldId="cluster-sync-mode" isRequired>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', paddingTop: '4px' }}>
            <Radio
              id="sync-mode-api"
              name="sync-mode"
              label="API Sync"
              description="Connect via OAuth2. Requires client credentials and access tokens."
              isChecked={syncMode === 'api'}
              onChange={() => setCluster({ sync_mode: 'api' })}
            />
            <Radio
              id="sync-mode-database"
              name="sync-mode"
              label="Direct Database"
              description="Read directly from AAP's PostgreSQL database. Requires a read-only database account."
              isChecked={syncMode === 'database'}
              onChange={() => setCluster({ sync_mode: 'database' })}
            />
          </div>
        </FormGroup>

        <FormGroup label="Protocol" fieldId="cluster-protocol" isRequired>
          <Select
            id="cluster-protocol"
            isOpen={protocolOpen}
            onOpenChange={setProtocolOpen}
            selected={cluster.protocol}
            onSelect={(_e, val) => { setCluster({ protocol: val as 'http' | 'https' }); setProtocolOpen(false); }}
            toggle={(ref: React.Ref<MenuToggleElement>) => (
              <MenuToggle ref={ref} onClick={() => setProtocolOpen(!protocolOpen)} isExpanded={protocolOpen}>
                {cluster.protocol}
              </MenuToggle>
            )}
          >
            <SelectList>
              <SelectOption value="https">https</SelectOption>
              <SelectOption value="http">http</SelectOption>
            </SelectList>
          </Select>
        </FormGroup>

        <FormGroup label="AAP Host" fieldId="cluster-address" isRequired>
          <TextInput
            id="cluster-address"
            value={cluster.address}
            onChange={(_e, v) => setCluster({ address: v })}
            placeholder="my-aap.example.com"
            isRequired
          />
          <FormHelperText>
            <HelperText>
              <HelperTextItem>Hostname or IP address — do not include protocol or port</HelperTextItem>
            </HelperText>
          </FormHelperText>
        </FormGroup>

        <FormGroup label="Port" fieldId="cluster-port" isRequired>
          <TextInput
            id="cluster-port"
            type="number"
            value={String(cluster.port)}
            onChange={(_e, v) => setCluster({ port: parseInt(v, 10) || 443 })}
            isRequired
          />
        </FormGroup>

        <FormGroup label="AAP Version" fieldId="cluster-version" isRequired>
          <Select
            id="cluster-version"
            isOpen={versionOpen}
            onOpenChange={setVersionOpen}
            selected={cluster.aap_version}
            onSelect={(_e, val) => { setCluster({ aap_version: val as AAPVersion }); setVersionOpen(false); }}
            toggle={(ref: React.Ref<MenuToggleElement>) => (
              <MenuToggle ref={ref} onClick={() => setVersionOpen(!versionOpen)} isExpanded={versionOpen}>
                {cluster.aap_version}
              </MenuToggle>
            )}
          >
            <SelectList>
              {AAP_VERSIONS.map((v) => <SelectOption key={v} value={v}>{v}</SelectOption>)}
            </SelectList>
          </Select>
        </FormGroup>

        {syncMode === 'api' && (
          <>
            <FormGroup label="Client ID" fieldId="cluster-client-id" isRequired>
              <TextInput
                id="cluster-client-id"
                value={cluster.client_id}
                onChange={(_e, v) => setCluster({ client_id: v })}
                isRequired
              />
              <FormHelperText>
                <HelperText>
                  <HelperTextItem>From the OAuth2 application you created in AAP Controller</HelperTextItem>
                </HelperText>
              </FormHelperText>
            </FormGroup>

            <FormGroup label="Client Secret" fieldId="cluster-client-secret" isRequired>
              <TextInput
                id="cluster-client-secret"
                type="password"
                value={cluster.client_secret}
                onChange={(_e, v) => setCluster({ client_secret: v })}
                isRequired
              />
            </FormGroup>
          </>
        )}

        <FormGroup label="Verify SSL" fieldId="cluster-verify-ssl">
          <Switch
            id="cluster-verify-ssl"
            label={cluster.verify_ssl ? 'Verify SSL certificate' : 'Skip SSL verification'}
            isChecked={cluster.verify_ssl}
            onChange={(_e, checked) => setCluster({ verify_ssl: checked })}
          />
        </FormGroup>

        {syncMode === 'api' && (
          <>
            {connectionError && (
              <Alert variant="danger" title={connectionError} isInline />
            )}
            {connectionTest === 'success' && (
              <Alert variant="success" title="Connection successful" isInline />
            )}

            <ActionGroup>
              <Button
                variant="secondary"
                onClick={handleTest}
                isDisabled={!cluster.address || !cluster.access_token || connectionTest === 'testing'}
              >
                {connectionTest === 'testing' ? <><Spinner size="sm" /> Testing...</> : 'Test Connection'}
              </Button>
            </ActionGroup>
          </>
        )}

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

export default StepCluster;
