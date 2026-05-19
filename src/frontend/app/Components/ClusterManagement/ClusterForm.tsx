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
  MenuToggle,
  MenuToggleElement,
  Radio,
  Select,
  SelectList,
  SelectOption,
  Spinner,
  Switch,
  TextInput,
} from '@patternfly/react-core';
import { ClusterFormData, ClusterInfo, AAPVersion } from '@app/Types/ClusterTypes';
import useClusterStore from '@app/Store/clusterStore';

interface ClusterFormProps {
  mode: 'add' | 'edit';
  cluster?: ClusterInfo;
  onSave: (data: ClusterFormData) => Promise<void>;
  onCancel: () => void;
}

const PROTOCOL_OPTIONS: Array<'http' | 'https'> = ['https', 'http'];
const VERSION_OPTIONS: AAPVersion[] = ['AAP 2.7', 'AAP 2.6', 'AAP 2.5', 'AAP 2.4'];

export const ClusterForm: React.FC<ClusterFormProps> = ({ mode, cluster, onSave, onCancel }) => {
  const testConnection = useClusterStore((s) => s.testConnection);
  const testDbConnection = useClusterStore((s) => s.testDbConnection);
  const connectionTest = useClusterStore((s) => s.connectionTest);
  const connectionError = useClusterStore((s) => s.connectionError);
  const saving = useClusterStore((s) => s.saving);

  const [syncMode, setSyncMode] = React.useState<'api' | 'database'>(cluster?.sync_mode ?? 'api');
  const [aapVersion, setAapVersion] = React.useState<AAPVersion>(cluster?.aap_version ?? 'AAP 2.5');

  // API mode fields
  const [protocol, setProtocol] = React.useState<'http' | 'https'>(cluster?.protocol ?? 'https');
  const [address, setAddress] = React.useState(cluster?.address ?? '');
  const [port, setPort] = React.useState<number>(cluster?.port ?? 443);
  const [verifySsl, setVerifySsl] = React.useState<boolean>(cluster?.verify_ssl ?? true);
  const [clientId, setClientId] = React.useState(cluster?.client_id ?? '');
  const [clientSecret, setClientSecret] = React.useState('');
  const [accessToken, setAccessToken] = React.useState('');
  const [refreshToken, setRefreshToken] = React.useState('');

  // Database mode fields
  const [dbHost, setDbHost] = React.useState(cluster?.db_host ?? '');
  const [dbPort, setDbPort] = React.useState<number>(cluster?.db_port ?? 5432);
  const [dbName, setDbName] = React.useState(cluster?.db_name ?? 'awx');
  const [dbUser, setDbUser] = React.useState(cluster?.db_user ?? '');
  const [dbPassword, setDbPassword] = React.useState('');

  const [isProtocolOpen, setIsProtocolOpen] = React.useState(false);
  const [isVersionOpen, setIsVersionOpen] = React.useState(false);

  const tokenPlaceholder = mode === 'edit' ? 'Leave blank to keep existing' : '';
  const dbPasswordPlaceholder = mode === 'edit' ? 'Leave blank to keep existing' : '';

  const handleSave = async () => {
    await onSave({
      sync_mode: syncMode,
      aap_version: aapVersion,
      // API mode fields — use db_host as address surrogate in database mode
      protocol: syncMode === 'database' ? 'https' : protocol,
      address: syncMode === 'database' ? dbHost : address,
      port: syncMode === 'database' ? dbPort : port,
      verify_ssl: syncMode === 'database' ? true : verifySsl,
      client_id: clientId,
      client_secret: clientSecret,
      access_token: accessToken,
      refresh_token: refreshToken,
      // Database mode fields
      db_host: dbHost,
      db_port: dbPort,
      db_name: dbName,
      db_user: dbUser,
      db_password: dbPassword,
    });
  };

  const handleTestApi = async () => {
    await testConnection({ protocol, address, port, access_token: accessToken, verify_ssl: verifySsl });
  };

  const handleTestDb = async () => {
    await testDbConnection({ db_host: dbHost, db_port: dbPort, db_name: dbName, db_user: dbUser, db_password: dbPassword });
  };

  return (
    <Form>
      {/* Sync Mode */}
      <FormGroup label="Sync Mode" isRequired fieldId="cluster-sync-mode">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', paddingTop: '4px' }}>
          <Radio
            id="form-sync-mode-api"
            name="form-sync-mode"
            label="API Sync"
            description="Connect via OAuth2. Requires client credentials and access tokens."
            isChecked={syncMode === 'api'}
            onChange={() => setSyncMode('api')}
          />
          <Radio
            id="form-sync-mode-database"
            name="form-sync-mode"
            label="Direct Database"
            description="Read directly from AAP's PostgreSQL database. Requires a read-only database account."
            isChecked={syncMode === 'database'}
            onChange={() => setSyncMode('database')}
          />
        </div>
      </FormGroup>

      {/* AAP Version — shown for both modes */}
      <FormGroup label="AAP Version" isRequired fieldId="cluster-version">
        <Select
          isOpen={isVersionOpen}
          onOpenChange={(open) => setIsVersionOpen(open)}
          onSelect={(_ev, value) => { setAapVersion(value as AAPVersion); setIsVersionOpen(false); }}
          selected={aapVersion}
          toggle={(ref: React.Ref<MenuToggleElement>) => (
            <MenuToggle ref={ref} onClick={() => setIsVersionOpen(!isVersionOpen)} isExpanded={isVersionOpen} style={{ width: '160px' }}>
              {aapVersion}
            </MenuToggle>
          )}
        >
          <SelectList>
            {VERSION_OPTIONS.map((opt) => <SelectOption key={opt} value={opt}>{opt}</SelectOption>)}
          </SelectList>
        </Select>
      </FormGroup>

      {/* API mode — host/port/SSL/credentials */}
      {syncMode === 'api' && (
        <>
          <FormGroup label="Protocol" isRequired fieldId="cluster-protocol">
            <Select
              isOpen={isProtocolOpen}
              onOpenChange={(open) => setIsProtocolOpen(open)}
              onSelect={(_ev, value) => { setProtocol(value as 'http' | 'https'); setIsProtocolOpen(false); }}
              selected={protocol}
              toggle={(ref: React.Ref<MenuToggleElement>) => (
                <MenuToggle ref={ref} onClick={() => setIsProtocolOpen(!isProtocolOpen)} isExpanded={isProtocolOpen} style={{ width: '160px' }}>
                  {protocol}
                </MenuToggle>
              )}
            >
              <SelectList>
                {PROTOCOL_OPTIONS.map((opt) => <SelectOption key={opt} value={opt}>{opt}</SelectOption>)}
              </SelectList>
            </Select>
          </FormGroup>

          <FormGroup label="Host" isRequired fieldId="cluster-address">
            <TextInput id="cluster-address" value={address} onChange={(_ev, val) => setAddress(val)} placeholder="aap.example.com" isRequired />
          </FormGroup>

          <FormGroup label="Port" isRequired fieldId="cluster-port">
            <TextInput id="cluster-port" type="number" value={String(port)} onChange={(_ev, val) => setPort(Number(val))} isRequired />
          </FormGroup>

          <FormGroup fieldId="cluster-verify-ssl">
            <Switch id="cluster-verify-ssl" label="Verify SSL" isChecked={verifySsl} onChange={(_ev, checked) => setVerifySsl(checked)} />
          </FormGroup>

          <FormGroup label="Client ID" isRequired fieldId="cluster-client-id">
            <TextInput id="cluster-client-id" value={clientId} onChange={(_ev, val) => setClientId(val)} isRequired />
          </FormGroup>

          <FormGroup label="Client Secret" fieldId="cluster-client-secret">
            <TextInput id="cluster-client-secret" type="password" value={clientSecret} onChange={(_ev, val) => setClientSecret(val)} placeholder={tokenPlaceholder} />
          </FormGroup>

          <FormGroup label="Access Token" fieldId="cluster-access-token">
            <TextInput id="cluster-access-token" type="password" value={accessToken} onChange={(_ev, val) => setAccessToken(val)} placeholder={tokenPlaceholder} />
          </FormGroup>

          <FormGroup label="Refresh Token" fieldId="cluster-refresh-token">
            <TextInput id="cluster-refresh-token" type="password" value={refreshToken} onChange={(_ev, val) => setRefreshToken(val)} placeholder={tokenPlaceholder} />
          </FormGroup>

          {connectionTest === 'success' && <Alert variant="success" isInline title="Connection successful" />}
          {connectionTest === 'failed' && <Alert variant="danger" isInline title={`Connection failed${connectionError ? `: ${connectionError}` : ''}`} />}

          <ActionGroup>
            <Button variant="secondary" onClick={handleTestApi} isDisabled={connectionTest === 'testing' || saving} icon={connectionTest === 'testing' ? <Spinner size="sm" /> : undefined}>
              {connectionTest === 'testing' ? 'Testing…' : 'Test Connection'}
            </Button>
          </ActionGroup>
        </>
      )}

      {/* Database mode — only DB credentials */}
      {syncMode === 'database' && (
        <>
          <FormGroup label="DB Host" isRequired fieldId="db-host">
            <TextInput id="db-host" value={dbHost} onChange={(_ev, val) => setDbHost(val.replace(/^https?:\/\//i, ''))} placeholder="44.201.211.61" isRequired />
            <FormHelperText><HelperText><HelperTextItem>IP address or hostname only — no <code>http://</code> or <code>https://</code></HelperTextItem></HelperText></FormHelperText>
          </FormGroup>

          <FormGroup label="DB Port" isRequired fieldId="db-port">
            <TextInput id="db-port" type="number" value={String(dbPort)} onChange={(_ev, val) => setDbPort(parseInt(val, 10) || 5432)} isRequired style={{ maxWidth: '120px' }} />
          </FormGroup>

          <FormGroup label="Database Name" isRequired fieldId="db-name">
            <TextInput id="db-name" value={dbName} onChange={(_ev, val) => setDbName(val)} placeholder="awx" isRequired />
          </FormGroup>

          <FormGroup label="DB User" isRequired fieldId="db-user">
            <TextInput id="db-user" value={dbUser} onChange={(_ev, val) => setDbUser(val)} isRequired />
          </FormGroup>

          <FormGroup label="DB Password" fieldId="db-password">
            <TextInput id="db-password" type="password" value={dbPassword} onChange={(_ev, val) => setDbPassword(val)} placeholder={dbPasswordPlaceholder} />
          </FormGroup>

          {connectionTest === 'success' && <Alert variant="success" isInline title="Database connection successful" />}
          {connectionTest === 'failed' && <Alert variant="danger" isInline title={`Connection failed${connectionError ? `: ${connectionError}` : ''}`} />}

          <ActionGroup>
            <Button variant="secondary" onClick={handleTestDb} isDisabled={connectionTest === 'testing' || saving || !dbHost || !dbUser} icon={connectionTest === 'testing' ? <Spinner size="sm" /> : undefined}>
              {connectionTest === 'testing' ? 'Testing…' : 'Test Connection'}
            </Button>
          </ActionGroup>
        </>
      )}

      <ActionGroup>
        <Button variant="primary" onClick={handleSave} isDisabled={saving || connectionTest === 'testing'} icon={saving ? <Spinner size="sm" /> : undefined}>
          {saving ? 'Saving…' : 'Save'}
        </Button>
        <Button variant="link" onClick={onCancel} isDisabled={saving}>Cancel</Button>
      </ActionGroup>
    </Form>
  );
};

export default ClusterForm;
