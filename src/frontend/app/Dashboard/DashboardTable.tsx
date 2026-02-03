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
  useAutomatedProcessCost,
  useManualCostAutomation
} from '@app/Store/filterSelectors';
import { useTranslation } from 'react-i18next';

export const DashboardTable: React.FunctionComponent<DashboardTableProps> = (props: DashboardTableProps) => {
  const { t } = useTranslation();
  const hourly_manual_costs = useManualCostAutomation();
  const hourly_automated_process_costs = useAutomatedProcessCost();
  const selectedCurrencySign = useCurrencySign();
  const [hourlyManualCostsChangedError, setHourlyManualCostsChangedError] = React.useState<string | null>(null);
  const [hourlyAutomatedProcessCostsChangedError, setHourlyAutomatedProcessCostsChangedError] = React.useState<
    string | null
  >(null);
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
        setHourlyManualCostsChangedError(t('Value must be greater than 0!'));
      } else if (value > 1000) {
        setHourlyManualCostsChangedError(t('Value must be less than or equal to 1000!'));
      } else {
        setHourlyManualCostsChangedError(null);
        props.onCostChanged('manual', value);
      }
    } else {
      setHourlyManualCostsChangedError(t('Please enter a valid number!'));
    }
  };

  const hourlyAutomatedProcessCostsChanged = (value: number | null | undefined) => {
    if (value || value === 0) {
      if (value <= 0) {
        setHourlyAutomatedProcessCostsChangedError(t('Value must be greater than 0!'));
      } else if (value > 1000) {
        setHourlyAutomatedProcessCostsChangedError(t('Value must be less than or equal to 1000!'));
      } else {
        setHourlyAutomatedProcessCostsChangedError(null);
        props.onCostChanged('automated', value);
      }
    } else {
      setHourlyAutomatedProcessCostsChangedError(t('Please enter a valid number!'));
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
      label={t('Include time taken to create automation into calculation')}
      id="switch-time-taken-automation"
      isChecked={switchEnableTemplateCreationTimeIsChecked}
      aria-checked={switchEnableTemplateCreationTimeIsChecked}
      onChange={handleSwitchEnableTemplateCreationTime}
    />
  );

  const columns: ColumnProps[] = [
    { name: 'name', title: t('Template Name'), isVisible: true },
    { name: 'runs', title: t('Number of job executions'), type: 'number', isVisible: true },
    { name: 'num_hosts', title: t('Host executions'), type: 'number', isVisible: true },
    {
      name: 'time_taken_manually_execute_minutes',
      title: t('Time taken to manually execute (min)'),
      info: { tooltip: t('Please enter an average time that an engineer would spend to run the job') },
      isEditable: true,
      isVisible: true
    },
    {
      name: 'time_taken_create_automation_minutes',
      title: t('Time taken to create automation (min)'),
      info: { tooltip: t('Please enter the time an engineer would spend to automate this job') },
      isEditable: true,
      isVisible: switchEnableTemplateCreationTimeIsChecked
    },
    { name: 'elapsed', title: t('Running time'), valueKey: 'elapsed_str', type: 'time-string', isVisible: true },
    { name: 'automated_costs', title: t('Automated cost'), type: 'currency', isVisible: true },
    { name: 'manual_costs', title: t('Manual cost'), type: 'currency', isVisible: true },
    { name: 'savings', title: t('Savings'), type: 'currency', isVisible: true }
  ];
  return (
    <>
      <Card>
        <CardBody>
          {props.loading && (
            <div className={'table-loader'}>
              <Spinner className={'spinner'} diameter="80px" aria-label={t('Loader')} />
            </div>
          )}
          <Flex className="pf-v6-u-mb-lg pf-v6-u-align-items-flex-start pf-m-row-gap-sm">
            <FlexItem>
              <Form onSubmit={(e) => e.preventDefault()}>
                <FormGroup
                  label={t('Hourly rate for manually running the job ({{currency}})', { currency: selectedCurrencySign })}
                  labelHelp={
                    <Tooltip content={t('Please enter an average cost per hour for the engineer manually running jobs')}>
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
                  label={t('Average cost per minute of running on AAP ({{currency}})', { currency: selectedCurrencySign })}
                  labelHelp={
                    <Tooltip content={t('Please enter an average cost per minute of running a job in the Ansible Automation Platform')}>
                      <Icon size="md" className="pf-v6-u-ml-sm">
                        <OutlinedQuestionCircleIcon />
                      </Icon>
                    </Tooltip>
                  }
                >
                  <CustomInput
                    type={'number'}
                    id={'hourly-automated-process-costs'}
                    onBlur={(value) => hourlyAutomatedProcessCostsChanged(value ? parseFloat(value) : value)}
                    value={hourly_automated_process_costs}
                    errorMessage={hourlyAutomatedProcessCostsChangedError}
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
                  {t('Export as CSV')}
                </Button>
              </FlexItem>
            )}
          </Flex>
          <Grid hasGutter className="pf-v6-u-mb-xl">
            <GridItem className="pf-m-12-col pf-m-6-col-on-md pf-m-3-col-on-2xl">
              <Card className="card">
                <CardBody>
                  <DashboardTotals
                    title={t('Cost of manual automation')}
                    result={formatCurrency(props?.costOfManualAutomation?.value, selectedCurrencySign)}
                    tooltip={t('Manual time of automation (minutes) * Host executions * Average cost of an employee minute')}
                  />
                </CardBody>
              </Card>
            </GridItem>
            <GridItem className="pf-m-12-col pf-m-6-col-on-md pf-m-3-col-on-2xl">
              <Card style={{ height: '100%' }}>
                <CardBody>
                  <DashboardTotals
                    title={t('Cost of automated execution')}
                    result={formatCurrency(props?.costOfAutomatedExecution?.value, selectedCurrencySign)}
                    tooltip={
                      switchEnableTemplateCreationTimeIsChecked
                        ? t('Running time (s) / 60 * Cost per minute of AAP + Time taken to create automation (minutes) * Average cost of an employee minute')
                        : t('Running time (s) / 60 * Cost per minute of AAP')
                    }
                  />
                </CardBody>
              </Card>
            </GridItem>
            <GridItem className="pf-m-12-col pf-m-6-col-on-md pf-m-3-col-on-2xl">
              <Card style={{ height: '100%' }}>
                <CardBody>
                  <DashboardTotals
                    title={t('Total savings/cost avoided')}
                    result={formatCurrency(props?.totalSaving?.value, selectedCurrencySign)}
                    tooltip={t('Cost of manual automation - Cost of automated execution')}
                  />
                </CardBody>
              </Card>
            </GridItem>
            <GridItem className="pf-m-12-col pf-m-6-col-on-md pf-m-3-col-on-2xl">
              <Card style={{ height: '100%' }}>
                <CardBody>
                  <DashboardTotals
                    title={t('Total hours saved/avoided')}
                    result={
                      props?.totalTimeSavings?.value || props?.totalTimeSavings?.value === 0
                        ? formatNumber(props.totalTimeSavings.value, 2) + 'h'
                        : ''
                    }
                    tooltip={
                      switchEnableTemplateCreationTimeIsChecked
                        ? t('Manual time of automation (minutes) * Host executions + Time taken to create automation (minutes) - Running time (s) / 60')
                        : t('Manual time of automation (minutes) * Host executions - Running time (s) / 60')
                    }
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
