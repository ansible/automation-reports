import React, { useContext } from 'react';
import { BaseTable } from '../Components/BaseTable';
import { Card, CardBody, Flex, FlexItem, Form, FormGroup, Icon, Spinner, Tooltip } from '@patternfly/react-core';
import { DashboardTotals } from './DashboardTotals';
import { OutlinedQuestionCircleIcon } from '@patternfly/react-icons';
import { CustomInput } from '@app/Components/CustomInput';
import { useAppSelector } from '@app/hooks';

import { automatedProcessCost, manualCostAutomation } from '@app/Store';
import { ParamsContext } from '@app/Store/paramsContext';
import '../styles/table.scss';
import { DashboardTableProps, columnProps } from '@app/Types';
import { formatCurrency } from '@app/Utils';

export const DashboardTable: React.FunctionComponent<DashboardTableProps> = (props: DashboardTableProps) => {
  const context = useContext(ParamsContext);
  if (!context) {
    throw new Error('Filters must be used within a ParamsProvider');
  }
  const { setParams } = context;

  const hourly_manual_costs = useAppSelector(manualCostAutomation);
  const hourly_automated_process_costs = useAppSelector(automatedProcessCost);

  const [hourlyManualCostsChangedError, setHourlyManualCostsChangedError] = React.useState<string | null>(null);
  const [hourlyAutomatedProcessCostsChangedError, setHourlyAutomatedProcessCostsChangedError] = React.useState<
    string | null
  >(null);

  const updateParams = (key, value) => {
    setParams((prevParams) => ({
      ...prevParams,
      [key]: value,
    }));
  };

  const handlePageChange = (newPage: number) => {
    updateParams('page', newPage);
  };

  const handlePerPageChange = (page: number, newPerPage: number) => {
    updateParams('page', page);
    updateParams('page_size', newPerPage);
  };

  const handleSort = (ordering: string) => {
    updateParams('page', 1);
    updateParams('ordering', ordering);
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

  const columns: columnProps[] = [
    { name: 'name', title: 'Name' },
    { name: 'successful_runs', title: 'Number of successful runs', type: 'number' },
    { name: 'failed_runs', title: 'Number of unsuccessful runs', type: 'number' },
    { name: 'runs', title: 'Runs', type: 'number' },
    { name: 'num_hosts', title: 'Number of hosts jobs were run on', type: 'number' },
    {
      name: 'manual_time',
      title: 'Manual time of automation (minutes)',
      info: { tooltip: 'Manual time of automation (minutes)' },
      isEditable: true,
    },
    { name: 'elapsed', title: 'Running time', valueKey: 'elapsed_str' },
    { name: 'savings', title: 'Savings', type: 'currency' },
    { name: 'automated_costs', title: 'Automated cost', type: 'currency' },
    { name: 'manual_costs', title: 'Manual cost', type: 'currency' },
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
          <Flex className="pf-v6-u-mb-2xl details-row">
            <Flex>
              <FlexItem>
                <Form>
                  <FormGroup
                    label="Hourly manual cost of automation ($)"
                    labelHelp={
                      <Tooltip content="Content">
                        <Icon size="md" className="pf-v6-u-ml-sm">
                          <OutlinedQuestionCircleIcon />
                        </Icon>
                      </Tooltip>
                    }
                  >
                    <CustomInput
                      type={'number'}
                      id={'hourly-manual-costs'}
                      onBlur={(value) => hourlyManualCostsChanged(value)}
                      errorMessage={hourlyManualCostsChangedError}
                      value={hourly_manual_costs}
                    />
                  </FormGroup>
                </Form>
              </FlexItem>
              <FlexItem>
                <Form>
                  <FormGroup
                    label="Hourly automated process cost ($)"
                    labelHelp={
                      <Tooltip content="Content">
                        <Icon size="md" className="pf-v6-u-ml-sm">
                          <OutlinedQuestionCircleIcon />
                        </Icon>
                      </Tooltip>
                    }
                  >
                    <CustomInput
                      type={'number'}
                      id={'hourly-automated-process-costs'}
                      onBlur={(value) => hourlyAutomatedProcessCostsChanged(value)}
                      value={hourly_automated_process_costs}
                      errorMessage={hourlyAutomatedProcessCostsChangedError}
                    />
                  </FormGroup>
                </Form>
              </FlexItem>
            </Flex>
            <Flex className="cards-gap">
              <FlexItem>
                <DashboardTotals
                  title={'Cost of manual automation'}
                  result={formatCurrency(props?.costOfManualAutomation?.value)}
                  percentage={props?.costOfManualAutomation?.index}
                />
              </FlexItem>
              <FlexItem>
                <DashboardTotals
                  title={'Cost of automated execution'}
                  result={formatCurrency(props?.costOfAutomatedExecution?.value)}
                  percentage={props?.costOfAutomatedExecution?.index}
                />
              </FlexItem>
              <FlexItem>
                <DashboardTotals
                  title={'Total savings'}
                  result={formatCurrency(props?.totalSaving?.value)}
                  percentage={props.totalSaving?.index}
                />
              </FlexItem>
            </Flex>
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
          ></BaseTable>
        </CardBody>
      </Card>
    </>
  );
};
