import * as React from 'react';
import { Alert, Button, Spinner, Title } from '@patternfly/react-core';
import { useNavigate } from 'react-router-dom';
import useSetupStore from '@app/Store/setupStore';

const StepProgress: React.FC = () => {
  const pollSyncProgress = useSetupStore((s) => s.pollSyncProgress);
  const syncProgress = useSetupStore((s) => s.syncProgress);
  const navigate = useNavigate();

  React.useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;

    const poll = async () => {
      try {
        const result = await pollSyncProgress();
        if (!result.has_synced) {
          timer = setTimeout(poll, 5000);
        }
      } catch {
        timer = setTimeout(poll, 10000);
      }
    };

    poll();
    return () => clearTimeout(timer);
  }, []);

  const synced = syncProgress?.has_synced;

  return (
    <div style={{ textAlign: 'center', padding: '32px 0' }}>
      <Title headingLevel="h2" size="lg" style={{ marginBottom: '24px' }}>
        {synced ? 'Setup Complete' : 'Syncing Job Data'}
      </Title>

      {!synced && (
        <>
          <Spinner diameter="60px" aria-label="Syncing data" style={{ marginBottom: '24px' }} />
          <p style={{ color: 'var(--pf-v6-global--Color--200)' }}>
            The initial sync is running in the background. This may take several minutes depending
            on how much historical data is being imported.
            {' '}Make sure the <code>run_dispatcher</code> process is running.
          </p>
        </>
      )}

      {synced && (
        <>
          <Alert
            variant="success"
            title="Initial sync complete"
            isInline
            style={{ marginBottom: '24px', textAlign: 'left' }}
          >
            {syncProgress?.last_synced && (
              <>Last synced up to: {new Date(syncProgress.last_synced).toLocaleString()}</>
            )}
          </Alert>
          <Button variant="primary" onClick={() => navigate('/')}>
            Go to Dashboard
          </Button>
        </>
      )}
    </div>
  );
};

export default StepProgress;
