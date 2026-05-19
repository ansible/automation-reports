import * as React from 'react';
import {
  ActionGroup,
  Button,
  Form,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem,
  Radio,
  TextInput,
  Title,
} from '@patternfly/react-core';
import useSetupStore from '@app/Store/setupStore';

interface StepSyncProps {
  onNext: () => void;
  onBack: () => void;
}

const StepSync: React.FC<StepSyncProps> = ({ onNext, onBack }) => {
  const sync = useSetupStore((s) => s.sync);
  const setSync = useSetupStore((s) => s.setSync);

  return (
    <div>
      <Title headingLevel="h2" size="lg" style={{ marginBottom: '16px' }}>
        Initial Sync Range
      </Title>
      <p style={{ marginBottom: '24px' }}>
        How far back should the dashboard pull job history on first sync? Larger ranges take longer to import.
      </p>

      <Form style={{ maxWidth: '480px' }}>
        <FormGroup role="radiogroup" isStack fieldId="sync-mode" label="Sync range">
          <Radio
            id="sync-mode-days"
            name="sync-mode"
            label="Last N days"
            isChecked={sync.mode === 'days'}
            onChange={() => setSync({ mode: 'days' })}
          />
          <Radio
            id="sync-mode-since"
            name="sync-mode"
            label="From a specific date"
            isChecked={sync.mode === 'since'}
            onChange={() => setSync({ mode: 'since' })}
          />
        </FormGroup>

        {sync.mode === 'days' && (
          <FormGroup label="Number of days" fieldId="sync-days" isRequired>
            <TextInput
              id="sync-days"
              type="number"
              value={String(sync.initial_sync_days)}
              onChange={(_e, v) => setSync({ initial_sync_days: Math.max(1, parseInt(v, 10) || 1) })}
              isRequired
              style={{ maxWidth: '120px' }}
            />
            <FormHelperText>
              <HelperText>
                <HelperTextItem>
                  Syncing more than 90 days may take several minutes depending on job count
                </HelperTextItem>
              </HelperText>
            </FormHelperText>
          </FormGroup>
        )}

        {sync.mode === 'since' && (
          <FormGroup label="Start date" fieldId="sync-since" isRequired>
            <TextInput
              id="sync-since"
              type="date"
              value={sync.initial_sync_since ?? ''}
              onChange={(_e, v) => setSync({ initial_sync_since: v || null })}
              isRequired
              style={{ maxWidth: '200px' }}
            />
          </FormGroup>
        )}

        <ActionGroup>
          <Button
            variant="primary"
            onClick={onNext}
            isDisabled={sync.mode === 'since' && !sync.initial_sync_since}
          >
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

export default StepSync;
