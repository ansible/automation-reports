import React from 'react';
import {
  Button,
  Card,
  CardBody,
  Flex,
  FlexItem,
  Form,
  FormGroup,
  Grid,
  GridItem,
  Icon,
  Spinner,
  Switch,
  Tooltip
} from '@patternfly/react-core';
import { OutlinedQuestionCircleIcon } from '@patternfly/react-icons';
import { BaseTable, CustomInput } from '@app/Components';
import '../styles/table.scss';
import { ColumnProps, DashboardTableProps } from '@app/Types';
import { formatCurrency, formatNumber } from '@app/Utils';
import { DashboardTotals } from '@app/Dashboard/DashboardTotals';
import {
  useCurrencySign,
  useEnableTemplateCreationTime
} from '@app/Store/commonSelectors';
import {
  useMonthlySubscriptionCost,
  useManualCostAutomation,
} from '@app/Store/filterSelectors';

export const DashboardTable: React.FunctionComponent<DashboardTableProps> = (props: DashboardTableProps) => {
  const hourly_manual_costs = useManualCostAutomation();
  const monthly_subscription_cost = useMonthlySubscriptionCost();
  const selectedCurrencySign = useCurrencySign();
  const [hourlyManualCostsChangedError, setHourlyManualCostsChangedError] = React.useState<string | null>(null);
  const [monthlySubscriptionCostChangedError, setMonthlySubscriptionCostChangedError] = React.useState<string | null>(
    null,
  );
  const switchEnableTemplateCreationTimeIsChecked = useEnableTemplateCreationTime();

  const handlePageChange = (newPage: number) => {
    props.onPaginationChange({ page: newPage, page_size: props.pagination.page_size });
  };

  const handlePerPageChange = (page: number, newPerPage: number) => {
    props.onPaginationChange({ page: page, page_size: newPerPage });
  };

  const handleSort = (ordering: string) => {
    props.onSortChange(ordering);
  };

  const hourlyManualCostsChanged = (value: number | null | undefined) => {
    if (value || value === 0) {
      if (value <= 0) {
        setHourlyManualCostsChangedError('Value must be greater then 0!');
      } else if (value > 1000) {
        setHourlyManualCostsChangedError('Value must be less than or equal to 1000!');
      } else {
        setHourlyManualCostsChangedError(null);
        props.onCostChanged('manual', value);
      }
    } else {
      setHourlyManualCostsChangedError('Please enter a valid number!');
    }
  };

  const monthlySubscriptionCostChanged = (value: number | null | undefined) => {
    if (value || value === 0) {
      if (value <= 0) {
        setMonthlySubscriptionCostChangedError('Value must be greater then 0!');
      } else if (value > 1000000) {
        setMonthlySubscriptionCostChangedError('Value must be less than or equal to 1000000!');
      } else {
        setMonthlySubscriptionCostChangedError(null);
        props.onCostChanged('automated', value);
      }
    }else{
      setMonthlySubscriptionCostChangedError('Please enter a valid number!');
    }
  };

  const exportToCsv = () => {
    props.onExportCsv();
  };

  const handleSwitchEnableTemplateCreationTime = (_event: React.FormEvent<HTMLInputElement>, checked: boolean) => {
    props.onEnableTemplateCreationTimeChange(checked);
  };

  const switchEnableTemplateCreationTime = (
    <Switch
      label="Include time taken to create automation into calculation"
      id="switch-time-taken-automation"
      isChecked={switchEnableTemplateCreationTimeIsChecked}
      aria-checked={switchEnableTemplateCreationTimeIsChecked}
      onChange={handleSwitchEnableTemplateCreationTime}
    />
  );

  const columns: ColumnProps[] = [
    { name: 'name', title: 'Template Name', isVisible: true },
    { name: 'runs', title: 'Number of job executions', type: 'number', isVisible: true },
    { name: 'num_hosts', title: 'Host executions', type: 'number', isVisible: true },
    {
      name: 'time_taken_manually_execute_minutes',
      title: 'Time taken to manually execute (min)',
      info: { tooltip: 'Estimated manual execution time in minutes' },
      isEditable: true,
      isVisible: true,
    },
    {
      name: 'time_taken_create_automation_minutes',
      title: 'Time taken to create automation (min)',
      info: {
        tooltip:
          'Estimated time spent creating or authoring the automation (e.g. writing playbooks, setting up jobs) before it could be run. Included in cost when the switch above is on.',
      },
      isEditable: true,
      isVisible: switchEnableTemplateCreationTimeIsChecked,
    },
    { name: 'elapsed', title: 'Running time', valueKey: 'elapsed_str', type: 'time-string', isVisible: true },
    { name: 'automated_costs', title: 'Automated cost', type: 'currency', isVisible: true },
    { name: 'manual_costs', title: 'Manual cost', type: 'currency', isVisible: true },
    { name: 'savings', title: 'Savings', type: 'currency', isVisible: true },
  ];
  return (
    <>
      <Card>
        <CardBody>
          {props.loading && (
            <div className={'table-loader'}>
              <Spinner className={'spinner'} diameter="80px" aria-label="Loader" />
            </div>
          )}
          <Flex className="pf-v6-u-mb-lg pf-v6-u-align-items-flex-start pf-m-row-gap-sm">
            <FlexItem>
              <Form onSubmit={(e) => e.preventDefault()}>
                <FormGroup
                  label={`Hourly rate for manually running the job (${selectedCurrencySign})`}
                  labelHelp={
                    <Tooltip content="The hourly labor cost used to estimate what it would cost to run these jobs manually. Used to calculate manual cost and savings in the table below.">
                      <Icon size="md" className="pf-v6-u-ml-sm">
                        <OutlinedQuestionCircleIcon />
                      </Icon>
                    </Tooltip>
                  }
                >
                  <CustomInput
                    type={'number'}
                    id={'hourly-manual-costs'}
                    onBlur={(value) => hourlyManualCostsChanged(value ? parseFloat(value) : value)}
                    errorMessage={hourlyManualCostsChangedError}
                    value={hourly_manual_costs}
                    onFocus={props.onInputFocus}
                  />
                </FormGroup>
              </Form>
            </FlexItem>
            <FlexItem>
              <Form onSubmit={(e) => e.preventDefault()}>
                <FormGroup
                  label={`Monthly AAP cost (${selectedCurrencySign})`}
                  labelHelp={
                    <Tooltip content="Monthly cost of running the Ansible Automation Platform. This value includes license, labor and infrastructure costs to run AAP. It is used to calculate the automation savings.">
                      <Icon size="md" className="pf-v6-u-ml-sm">
                        <OutlinedQuestionCircleIcon />
                      </Icon>
                    </Tooltip>
                  }
                >
                  <CustomInput
                    type={'number'}
                    id={'monthly-subscription-cost'}
                    onBlur={(value) => monthlySubscriptionCostChanged(value ? parseFloat(value) : value)}
                    value={monthly_subscription_cost}
                    errorMessage={monthlySubscriptionCostChangedError}
                    onFocus={props.onInputFocus}
                  />
                </FormGroup>
              </Form>
            </FlexItem>
            <FlexItem className={'switch-time-taken-automation pf-v6-u-mt-xl-on-lg'}>
              {switchEnableTemplateCreationTime}
            </FlexItem>
            {props.data.count > 0 && (
              <FlexItem
                className={
                  'pf-v6-u-ml-auto-on-lg pf-v6-u-w-100-on-sm pf-v6-u-w-auto-on-lg pf-v6-u-mt-sm-on-sm pf-v6-u-mt-0-on-lg'
                }
              >
                <Button id={'csv-export'} onClick={exportToCsv} variant="secondary" isInline>
                  Export as CSV
                </Button>
              </FlexItem>
            )}
          </Flex>
          <Grid hasGutter className="pf-v6-u-mb-xl">
            <GridItem className="pf-m-12-col pf-m-6-col-on-md pf-m-3-col-on-2xl">
              <Card className="card">
                <CardBody>
                  <DashboardTotals
                    title={'Cost of manual automation'}
                    result={formatCurrency(props?.costOfManualAutomation?.value, selectedCurrencySign)}
                    tooltip={'Total cost if all jobs were run manually'}
                  />
                </CardBody>
              </Card>
            </GridItem>
            <GridItem className="pf-m-12-col pf-m-6-col-on-md pf-m-3-col-on-2xl">
              <Card style={{ height: '100%' }}>
                <CardBody>
                  <DashboardTotals
                    title={'Cost of automated execution'}
                    result={formatCurrency(props?.costOfAutomatedExecution?.value, selectedCurrencySign)}
                    tooltip={'Total cost of running jobs on AAP'}
                  />
                </CardBody>
              </Card>
            </GridItem>
            <GridItem className="pf-m-12-col pf-m-6-col-on-md pf-m-3-col-on-2xl">
              <Card style={{ height: '100%' }}>
                <CardBody>
                  <DashboardTotals
                    title={'Total savings/cost avoided'}
                    result={formatCurrency(props?.totalSaving?.value, selectedCurrencySign)}
                    tooltip={'Difference between manual and automated cost'}
                  />
                </CardBody>
              </Card>
            </GridItem>
            <GridItem className="pf-m-12-col pf-m-6-col-on-md pf-m-3-col-on-2xl">
              <Card style={{ height: '100%' }}>
                <CardBody>
                  <DashboardTotals
                    title={'Total hours saved/avoided'}
                    result={
                      props?.totalTimeSavings?.value || props?.totalTimeSavings?.value === 0
                        ? formatNumber(props.totalTimeSavings.value, 2) + 'h'
                        : ''
                    }
                    tooltip={'Time saved by automation vs manual execution'}
                  />
                </CardBody>
              </Card>
            </GridItem>
          </Grid>
          <BaseTable
            pagination={{
              onPageChange: handlePageChange,
              onPerPageChange: handlePerPageChange,
              totalItems: props.data.count,
              currentPage: props.pagination.page,
              perPage: props.pagination.page_size,
            }}
            data={props.data.results}
            sort={{ onSortChange: handleSort }}
            columns={columns}
            loading={false}
            onItemEdit={props.onItemEdit}
            onItemFocus={props.onInputFocus}
            className={switchEnableTemplateCreationTimeIsChecked ? '' : 'less'}
          ></BaseTable>
        </CardBody>
      </Card>
    </>
  );
};
