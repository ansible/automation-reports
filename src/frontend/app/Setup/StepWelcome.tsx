import * as React from 'react';
import { Button } from '@patternfly/react-core';
import { CheckCircleIcon, CubesIcon, KeyIcon, ClockIcon, CogIcon } from '@patternfly/react-icons';

interface StepWelcomeProps {
  onNext: () => void;
}

interface PrereqCardProps {
  icon: React.ReactNode;
  title: string;
  description: React.ReactNode;
}

const PrereqCard: React.FC<PrereqCardProps> = ({ icon, title, description }) => (
  <div style={{
    display: 'flex',
    gap: '16px',
    padding: '16px',
    borderRadius: '8px',
    border: '1px solid var(--pf-v6-global--BorderColor--100)',
    background: 'var(--pf-v6-global--BackgroundColor--100)',
    marginBottom: '12px',
  }}>
    <div style={{
      width: '36px',
      height: '36px',
      borderRadius: '8px',
      background: 'var(--pf-v6-global--primary-color--100)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#fff',
      flexShrink: 0,
      fontSize: '1rem',
    }}>
      {icon}
    </div>
    <div>
      <div style={{ fontWeight: 600, marginBottom: '4px', fontSize: '0.9rem' }}>{title}</div>
      <div style={{ color: 'var(--pf-v6-global--Color--200)', fontSize: '0.85rem', lineHeight: 1.5 }}>
        {description}
      </div>
    </div>
  </div>
);

const StepWelcome: React.FC<StepWelcomeProps> = ({ onNext }) => (
  <div>
    <p style={{ fontSize: '0.95rem', color: 'var(--pf-v6-global--Color--200)', marginBottom: '32px', lineHeight: 1.6 }}>
      This wizard connects the dashboard to your Ansible Automation Platform (AAP) cluster
      and starts syncing job data. It takes about 5 minutes.
    </p>

    <div style={{ marginBottom: '8px', fontWeight: 600, fontSize: '0.85rem', color: 'var(--pf-v6-global--Color--200)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
      Before you begin, you will need
    </div>
    <div style={{ marginBottom: '32px' }}>
      <PrereqCard
        icon={<CubesIcon />}
        title="OAuth2 application in AAP Controller"
        description={
          <>
            Create an app with grant type <strong>authorization-code</strong> and
            client type <strong>Confidential</strong>. Note the <strong>client_id</strong> and <strong>client_secret</strong>.
          </>
        }
      />
      <PrereqCard
        icon={<KeyIcon />}
        title="Access and refresh tokens"
        description={
          <>
            Create a token in AAP for that OAuth2 application with scope <strong>Read</strong>.
            Copy both the access token and refresh token — the refresh token is shown only once.
          </>
        }
      />
      <PrereqCard
        icon={<CogIcon />}
        title="AAP Controller host and version"
        description="The hostname or IP address of your AAP Controller, and whether it is version 2.4, 2.5, or 2.6."
      />
      <PrereqCard
        icon={<ClockIcon />}
        title="How far back to sync job history"
        description="You'll choose how many days of historical job data to import on first sync. More days means a longer initial import."
      />
    </div>

    <div style={{
      padding: '12px 16px',
      borderRadius: '6px',
      background: 'rgba(0, 102, 204, 0.08)',
      border: '1px solid rgba(0, 102, 204, 0.2)',
      marginBottom: '32px',
      fontSize: '0.85rem',
      color: 'var(--pf-v6-global--Color--200)',
      display: 'flex',
      alignItems: 'flex-start',
      gap: '10px',
    }}>
      <CheckCircleIcon style={{ color: 'var(--pf-v6-global--primary-color--100)', marginTop: '1px', flexShrink: 0 }} />
      <span>
        At the end you can also download a pre-filled <code>inventory</code> file
        for use with the Ansible-based installer.
      </span>
    </div>

    <Button variant="primary" size="lg" onClick={onNext}>
      Get Started →
    </Button>
  </div>
);

export default StepWelcome;
