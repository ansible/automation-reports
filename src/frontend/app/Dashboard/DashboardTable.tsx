import React from 'react';
import {
  Button,
  Card,
  CardBody,
  Flex,
  FlexItem,
  Form,
  FormGroup,
  Icon,
  Spinner,
  Tooltip,
} from '@patternfly/react-core';
import { DashboardTotals } from './DashboardTotals';
import { OutlinedQuestionCircleIcon } from '@patternfly/react-icons';
import { BaseTable, CustomInput } from '@app/Components';
import { useAppSelector } from '@app/hooks';

import { automatedProcessCost, currencySign, manualCostAutomation } from '@app/Store';
import '../styles/table.scss';
import { ColumnProps, DashboardTableProps } from '@app/Types';
import { formatCurrency } from '@app/Utils';

export const DashboardTable: React.FunctionComponent<DashboardTableProps> = (props: DashboardTableProps) => {
  const hourly_manual_costs = useAppSelector(manualCostAutomation);
  const hourly_automated_process_costs = useAppSelector(automatedProcessCost);
  const selectedCurrencySign = useAppSelector(currencySign);

  const [hourlyManualCostsChangedError, setHourlyManualCostsChangedError] = React.useState<string | null>(null);
  const [hourlyAutomatedProcessCostsChangedError, setHourlyAutomatedProcessCostsChangedError] = React.useState<
    string | null
  >(null);

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
      } else {
        setHourlyManualCostsChangedError(null);
        props.onCostChanged('manual', value);
      }
    }
  };

  const hourlyAutomatedProcessCostsChanged = (value: number | null | undefined) => {
    if (value || value === 0) {
      if (value <= 0) {
        setHourlyAutomatedProcessCostsChangedError('Value must be greater then 0!');
      } else {
        setHourlyAutomatedProcessCostsChangedError(null);
        props.onCostChanged('automated', value);
      }
    }
  };

  const exportToCsv = () => {
    props.onExportCsv();
  };

  const columns: ColumnProps[] = [
    { name: 'name', title: 'Name' },
    { name: 'runs', title: 'Number of job executions', type: 'number' },
    { name: 'num_hosts', title: 'Host executions', type: 'number' },
    {
      name: 'time_taken_manually_execute_minutes',
      title: 'Time taken to manually execute (minutes)',
      info: { tooltip: 'Please enter an average time that an engineer would spend to run the job' },
      isEditable: true,
    },
    {
      name: 'time_taken_create_automation_minutes',
      title: 'Time taken to create automation (minutes)',
      info: { tooltip: 'Please enter the time that an engineer would spend to automatize this job' },
      isEditable: true,
    },
    { name: 'elapsed', title: 'Running time', valueKey: 'elapsed_str' },
    { name: 'automated_costs', title: 'Automated cost', type: 'currency' },
    { name: 'manual_costs', title: 'Manual cost', type: 'currency' },
    { name: 'savings', title: 'Savings', type: 'currency' },
  ];

  return (
    <>
      <Card className="dashboard-table">
        <CardBody>
          {props.loading && (
            <div className={'table-loader'}>
              <Spinner className={'spinner'} diameter="80px" aria-label="Loader" />
            </div>
          )}

          <Flex className="pf-v6-u-mb-2xl pf-v6-u-align-items-flex-end">
            <FlexItem>
              <Form>
                <FormGroup
                  label={`Average cost of an employee minute (${selectedCurrencySign})`}
                  labelHelp={
                    <Tooltip content="Please enter an average cost per minute for the engineer manually running jobs">
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
              <Form>
                <FormGroup
                  label={`Cost per minute of AAP (${selectedCurrencySign})`}
                  labelHelp={
                    <Tooltip content="Please enter an average cost per minute of running a job in the Ansible Automation Platform">
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
            {props.data.count > 0 && (
              <FlexItem style={{ marginLeft: 'auto' }}>
                <Button id={'csv-export'} onClick={exportToCsv} variant="secondary" isInline>
                  Export as CSV
                </Button>
              </FlexItem>
            )}
          </Flex>
          <Flex className="cards-gap pf-v6-u-mb-2xl details-row">
            <FlexItem>
              <DashboardTotals
                title={'Cost of manual automation'}
                result={formatCurrency(props?.costOfManualAutomation?.value, selectedCurrencySign)}
                percentage={props?.costOfManualAutomation?.index}
                tooltip={'Manual time of automation (minutes) * Host executions * Average cost of an employee minute'}
              />
            </FlexItem>
            <FlexItem>
              <DashboardTotals
                title={'Cost of automated execution'}
                result={formatCurrency(props?.costOfAutomatedExecution?.value, selectedCurrencySign)}
                percentage={props?.costOfAutomatedExecution?.index}
                tooltip={
                  'Running time (s) / 60 * Cost per minute of AAP + Time taken to create automation (minutes) * Average cost of an employee minute'
                }
              />
            </FlexItem>
            <FlexItem>
              <DashboardTotals
                title={'Total savings/cost avoided'}
                result={formatCurrency(props?.totalSaving?.value, selectedCurrencySign)}
                percentage={props.totalSaving?.index}
                tooltip={'Cost of manual automation - Cost of automated execution'}
              />
            </FlexItem>
            <FlexItem>
              <DashboardTotals
                title={'Total hours saved/avoided'}
                result={props?.totalTimeSavings?.value}
                percentage={props.totalTimeSavings?.index}
                tooltip={
                  'Manual time of automation (minutes) * Host executions  + Time taken to create automation (minutes) - Running time (s) / 60'
                }
              />
            </FlexItem>
          </Flex>

          <BaseTable
            pagination={{
              onPageChange: handlePageChange,
              onPerPageChange: handlePerPageChange,
              totalItems: props.data.count,
            }}
            data={props.data.results}
            sort={{ onSortChange: handleSort }}
            columns={columns}
            loading={false}
            onItemEdit={props.onItemEdit}
            onItemFocus={props.onInputFocus}
          ></BaseTable>
        </CardBody>
      </Card>
    </>
  );
};
