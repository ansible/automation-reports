import * as React from 'react';
import { Alert, Spinner } from '@patternfly/react-core';
import useSetupStore from '@app/Store/setupStore';
import logo from '../../assets/images/logo.svg';
import LocalLoginForm from './LocalLoginForm';
import StepWelcome from './StepWelcome';
import StepCluster from './StepCluster';
import StepTokens from './StepTokens';
import StepDatabase from './StepDatabase';
import StepSync from './StepSync';
import StepInfra from './StepInfra';
import StepCosts from './StepCosts';
import StepReview from './StepReview';
import StepProgress from './StepProgress';

type Step = 'welcome' | 'cluster' | 'tokens' | 'database' | 'sync' | 'infra' | 'costs' | 'review' | 'progress';

const STEP_LABELS: Record<Step, string> = {
  welcome: 'Welcome',
  cluster: 'Cluster Connection',
  tokens: 'OAuth Tokens',
  database: 'Database Connection',
  sync: 'Sync Range',
  infra: 'Infrastructure',
  costs: 'Cost Settings',
  review: 'Review & Apply',
  progress: 'Progress',
};

interface SidebarProps {
  current: Step;
  username: string;
  steps: Step[];
}

const Sidebar: React.FC<SidebarProps> = ({ current, username, steps }) => {
  const stepIndex = (s: Step) => steps.indexOf(s);

  return (
    <div style={{
      width: '260px',
      minWidth: '260px',
      background: 'var(--pf-v6-global--BackgroundColor--dark-100)',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
    }}>
      {/* Header */}
      <div style={{ padding: '28px 24px 24px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
        <img src={logo} alt="Ansible Automation Platform" style={{ height: '36px', marginBottom: '16px', display: 'block' }} />
        <div style={{ color: '#fff', fontWeight: 600, fontSize: '1rem', lineHeight: 1.3 }}>
          Automation Dashboard
        </div>
        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.8rem', marginTop: '2px' }}>
          Setup Wizard
        </div>
      </div>

      {/* Steps */}
      <nav style={{ flex: 1, padding: '16px 12px', overflowY: 'auto' }}>
        {steps.map((s, idx) => {
          const ci = stepIndex(current);
          const done = idx < ci;
          const active = s === current;
          const future = idx > ci;

          return (
            <div
              key={s}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '9px 12px',
                borderRadius: '6px',
                marginBottom: '2px',
                background: active ? 'rgba(255,255,255,0.12)' : 'transparent',
                transition: 'background 0.15s',
              }}
            >
              <span style={{
                width: '22px',
                height: '22px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.7rem',
                fontWeight: 700,
                flexShrink: 0,
                background: done
                  ? 'var(--pf-v6-global--success-color--100)'
                  : active
                    ? 'var(--pf-v6-global--primary-color--100)'
                    : 'rgba(255,255,255,0.15)',
                color: '#fff',
              }}>
                {done ? '✓' : idx + 1}
              </span>
              <span style={{
                fontSize: '0.85rem',
                fontWeight: active ? 600 : 400,
                color: active
                  ? '#fff'
                  : done
                    ? 'rgba(255,255,255,0.8)'
                    : future
                      ? 'rgba(255,255,255,0.4)'
                      : 'rgba(255,255,255,0.6)',
                lineHeight: 1.3,
              }}>
                {STEP_LABELS[s]}
              </span>
            </div>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '16px 24px',
        borderTop: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
      }}>
        <div style={{
          width: '28px', height: '28px',
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.15)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontSize: '0.75rem', fontWeight: 600,
        }}>
          {username.slice(0, 1).toUpperCase()}
        </div>
        <div>
          <div style={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.8rem', fontWeight: 500 }}>{username}</div>
          <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.7rem' }}>Administrator</div>
        </div>
      </div>
    </div>
  );
};

const SetupWizard: React.FC = () => {
  const fetchSetupMe = useSetupStore((s) => s.fetchSetupMe);
  const setupMe = useSetupStore((s) => s.setupMe);
  const configure = useSetupStore((s) => s.configure);
  const configureStatus = useSetupStore((s) => s.configureStatus);
  const cluster = useSetupStore((s) => s.cluster);

  const [loading, setLoading] = React.useState(true);
  const [step, setStep] = React.useState<Step>('welcome');

  // Dynamic step list based on sync_mode
  const steps = React.useMemo<Step[]>(() => {
    const base: Step[] = ['welcome', 'cluster'];
    if (cluster.sync_mode === 'database') {
      base.push('database');
    } else {
      base.push('tokens');
    }
    return [...base, 'sync', 'infra', 'costs', 'review', 'progress'];
  }, [cluster.sync_mode]);

  const stepIndex = (s: Step) => steps.indexOf(s);

  React.useEffect(() => {
    fetchSetupMe().finally(() => setLoading(false));
  }, []);

  // If the current step is no longer in the dynamic list (e.g. sync_mode changed),
  // fall back to the previous valid step.
  React.useEffect(() => {
    if (stepIndex(step) === -1) {
      setStep('cluster');
    }
  }, [steps]);

  const next = () => {
    const idx = stepIndex(step);
    if (idx < steps.length - 1) setStep(steps[idx + 1]);
  };

  const back = () => {
    const idx = stepIndex(step);
    if (idx > 0) setStep(steps[idx - 1]);
  };

  const handleApply = async () => {
    try {
      await configure();
      setStep('progress');
    } catch {
      // error shown in StepReview
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spinner aria-label="Loading" />
      </div>
    );
  }

  if (!setupMe?.authenticated || !setupMe?.is_superuser) {
    return <LocalLoginForm onAuthenticated={() => fetchSetupMe()} />;
  }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar current={step} username={setupMe.username ?? 'admin'} steps={steps} />

      {/* Content area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        background: 'var(--pf-v6-global--BackgroundColor--100)',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Content header bar */}
        <div style={{
          padding: '20px 48px',
          borderBottom: '1px solid var(--pf-v6-global--BorderColor--100)',
          background: 'var(--pf-v6-global--BackgroundColor--100)',
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--pf-v6-global--Color--200)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '2px' }}>
            Step {stepIndex(step) + 1} of {steps.length}
          </div>
          <div style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--pf-v6-global--Color--100)' }}>
            {STEP_LABELS[step]}
          </div>
        </div>

        {/* Step content */}
        <div style={{ flex: 1, padding: '40px 48px', maxWidth: '680px' }}>
          {configureStatus === 'success' && step !== 'progress' && (
            <Alert variant="success" title="Configuration saved" isInline style={{ marginBottom: '24px' }} />
          )}

          {step === 'welcome' && <StepWelcome onNext={next} />}
          {step === 'cluster' && <StepCluster onNext={next} onBack={back} />}
          {step === 'tokens' && <StepTokens onNext={next} onBack={back} />}
          {step === 'database' && <StepDatabase onNext={next} onBack={back} />}
          {step === 'sync' && <StepSync onNext={next} onBack={back} />}
          {step === 'infra' && <StepInfra onNext={next} onBack={back} />}
          {step === 'costs' && <StepCosts onNext={next} onBack={back} />}
          {step === 'review' && <StepReview onApply={handleApply} onBack={back} />}
          {step === 'progress' && <StepProgress />}
        </div>
      </div>
    </div>
  );
};

export default SetupWizard;
