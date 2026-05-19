import * as React from 'react';
import {
  Alert,
  Button,
  DescriptionList,
  DescriptionListDescription,
  DescriptionListGroup,
  DescriptionListTerm,
  Spinner,
  Title,
} from '@patternfly/react-core';
import useSetupStore from '@app/Store/setupStore';

interface StepReviewProps {
  onApply: () => void;
  onBack: () => void;
}

const StepReview: React.FC<StepReviewProps> = ({ onApply, onBack }) => {
  const cluster = useSetupStore((s) => s.cluster);
  const sync = useSetupStore((s) => s.sync);
  const costs = useSetupStore((s) => s.costs);
  const configureStatus = useSetupStore((s) => s.configureStatus);
  const configureError = useSetupStore((s) => s.configureError);
  const downloadInventory = useSetupStore((s) => s.downloadInventory);
  const infra = useSetupStore((s) => s.infra);

  const [downloading, setDownloading] = React.useState(false);

  const syncLabel =
    sync.mode === 'days'
      ? `Last ${sync.initial_sync_days} days`
      : `From ${sync.initial_sync_since}`;

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadInventory();
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div>
      <Title headingLevel="h2" size="lg" style={{ marginBottom: '16px' }}>
        Review Configuration
      </Title>
      <p style={{ marginBottom: '24px' }}>
        Review the settings below, then click <strong>Apply Configuration</strong> to save and start
        the initial sync. You can also download a pre-filled inventory file for the Ansible installer.
      </p>

      <DescriptionList isHorizontal style={{ marginBottom: '32px', maxWidth: '560px' }}>
        <DescriptionListGroup>
          <DescriptionListTerm>AAP Host</DescriptionListTerm>
          <DescriptionListDescription>
            {cluster.protocol}://{cluster.address}:{cluster.port}
          </DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>AAP Version</DescriptionListTerm>
          <DescriptionListDescription>{cluster.aap_version}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>Client ID</DescriptionListTerm>
          <DescriptionListDescription>{cluster.client_id}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>SSL Verification</DescriptionListTerm>
          <DescriptionListDescription>{cluster.verify_ssl ? 'Enabled' : 'Disabled'}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>Initial Sync</DescriptionListTerm>
          <DescriptionListDescription>{syncLabel}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>Monthly Cost</DescriptionListTerm>
          <DescriptionListDescription>{costs.monthly_subscription_cost}</DescriptionListDescription>
        </DescriptionListGroup>
        <DescriptionListGroup>
          <DescriptionListTerm>Engineer Hourly Rate</DescriptionListTerm>
          <DescriptionListDescription>{costs.engineer_avg_hourly_rate}</DescriptionListDescription>
        </DescriptionListGroup>
      </DescriptionList>

      {configureError && (
        <Alert variant="danger" title={configureError} isInline style={{ marginBottom: '16px' }} />
      )}

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <Button
          variant="primary"
          onClick={onApply}
          isDisabled={configureStatus === 'pending' || configureStatus === 'success'}
        >
          {configureStatus === 'pending'
            ? <><Spinner size="sm" aria-label="Applying" /> Applying...</>
            : 'Apply Configuration'}
        </Button>

        <Button
          variant="secondary"
          onClick={handleDownload}
          isDisabled={downloading || !infra.dashboard_host}
          title={!infra.dashboard_host ? 'Complete the Infrastructure step to enable download' : undefined}
        >
          {downloading ? <><Spinner size="sm" /> Generating...</> : 'Download inventory File'}
        </Button>

        <Button variant="link" onClick={onBack} isDisabled={configureStatus === 'pending'}>
          Back
        </Button>
      </div>

      {!infra.dashboard_host && (
        <p style={{ marginTop: '8px', fontSize: '0.875rem', color: 'var(--pf-v6-global--Color--200)' }}>
          Fill in the Infrastructure step to enable the inventory file download.
        </p>
      )}
    </div>
  );
};

export default StepReview;
