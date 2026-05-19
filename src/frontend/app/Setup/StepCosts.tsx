import * as React from 'react';
import {
  ActionGroup,
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

interface StepCostsProps {
  onNext: () => void;
  onBack: () => void;
}

const StepCosts: React.FC<StepCostsProps> = ({ onNext, onBack }) => {
  const costs = useSetupStore((s) => s.costs);
  const setCosts = useSetupStore((s) => s.setCosts);

  const isValid =
    costs.monthly_subscription_cost > 0 &&
    costs.engineer_avg_hourly_rate > 0;

  return (
    <div>
      <Title headingLevel="h2" size="lg" style={{ marginBottom: '16px' }}>
        Cost Settings
      </Title>
      <p style={{ marginBottom: '24px' }}>
        These values are used to calculate automation savings in the dashboard reports. You can change
        them later from the dashboard.
      </p>

      <Form style={{ maxWidth: '420px' }}>
        <FormGroup label="Monthly AAP Subscription Cost" fieldId="cost-monthly" isRequired>
          <TextInput
            id="cost-monthly"
            type="number"
            value={String(costs.monthly_subscription_cost)}
            onChange={(_e, v) => setCosts({ monthly_subscription_cost: parseFloat(v) || 0 })}
            isRequired
          />
          <FormHelperText>
            <HelperText>
              <HelperTextItem>
                Total monthly cost of running AAP — includes license, labor, and infrastructure
              </HelperTextItem>
            </HelperText>
          </FormHelperText>
        </FormGroup>

        <FormGroup label="Engineer Average Hourly Rate" fieldId="cost-hourly" isRequired>
          <TextInput
            id="cost-hourly"
            type="number"
            value={String(costs.engineer_avg_hourly_rate)}
            onChange={(_e, v) => setCosts({ engineer_avg_hourly_rate: parseFloat(v) || 0 })}
            isRequired
          />
          <FormHelperText>
            <HelperText>
              <HelperTextItem>
                Average hourly rate for engineers performing manual tasks (used to calculate manual vs automated cost)
              </HelperTextItem>
            </HelperText>
          </FormHelperText>
        </FormGroup>

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

export default StepCosts;
