import React, { useContext, useEffect } from 'react';
import { BaseTable } from '../Components/BaseTable';
import { Card, CardBody, Flex, FlexItem, Form, FormGroup, Icon, Tooltip } from '@patternfly/react-core';
import { DashboardTotals } from './DashboardTotals';
import { OutlinedQuestionCircleIcon } from '@patternfly/react-icons';
import { CustomInput } from '@app/Components/CustomInput';
import { useAppDispatch, useAppSelector } from '@app/hooks';
import { costOfAutomatedExecution, costOfManualAutomation, fetchReports, totalSavings } from '@app/Store';
import { automatedProcessCost, manualCostAutomation, reportResults, reportsLoading } from '@app/Store';
import { ParamsContext } from '@app/Store/paramsContext';
import '../styles/table.scss';
import { columnProps } from '@app/Types';

export const DashboardTable: React.FunctionComponent = () => {
  const context = useContext(ParamsContext);
  if (!context) {
    throw new Error('Filters must be used within a ParamsProvider');
  }
  const { params, setParams } = context;

  const hourly_manual_costs = useAppSelector(manualCostAutomation);
  const hourly_automated_process_costs = useAppSelector(automatedProcessCost);
  const loadingReports = useAppSelector(reportsLoading);
  const manual_automation_cost = useAppSelector(costOfManualAutomation) || { value: null, index: null };
  const automated_execution_cost = useAppSelector(costOfAutomatedExecution) || { value: null, index: null };
  const total_savings = useAppSelector(totalSavings) || { value: null, index: null };

  const dispatch = useAppDispatch();
  const reportsList = useAppSelector(reportResults);

  useEffect(() => {
    fetchServerData();
  }, [dispatch, params]);

  const fetchServerData = async () => {
    await dispatch(fetchReports(params));
  };

  const updateParams = (key, value) => {
    setParams((prevParams) => ({
      ...prevParams,
      [key]: value
    }));
  };

  const handlePageChange = (newPage: number) => {
    updateParams('page', newPage);
  };

  const handlePerPageChange = (page: number, newPerPage: number) => {
    updateParams('page', page);
    updateParams('page_size', newPerPage);
  };

  const handleSort = (ordering) => {
    updateParams('ordering', ordering);
  };

  // const handleInputChange = (value, rowIndex, columnName) => {
  //   if (value) {
  //     console.log('INPUT CHANGED', value, rowIndex, columnName);
  //   }
  // }

  const handleBlur = (value) => {
    if (value) {
      console.log('Handle blur - event', value);
    }
  };

  const columns: columnProps[] = [
    { name: 'name', title: 'Name' },
    { name: 'successful_runs', title: 'Number of successful runs', type: 'number' },
    { name: 'failed_runs', title: 'Number of unsuccessful runs', type: 'number' },
    { name: 'runs', title: 'Runs', type: 'number' },
    { name: 'num_hosts', title: 'Number of hosts jobs were run on', type: 'number' },
    { name: 'manual_time', title: 'Manual time of automation (minutes)', info: { tooltip: 'Manual time of automation (minutes)' }, isEditable: true },
    { name: 'savings', title: 'Savings', type: 'currency' },
    { name: 'automated_costs', title: 'Automated cost', type: 'currency' },
    { name: 'manual_costs', title: 'Manual cost', type: 'currency' }
  ];

  return (
    <>
      <Card className="dashboard-table">
        <CardBody>
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
                      onBlur={(value) => handleBlur(value)}
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
                      onBlur={(value) => handleBlur(value)}
                      value={hourly_automated_process_costs}
                    />
                  </FormGroup>
                </Form>
              </FlexItem>
            </Flex>
            <Flex className="cards-gap">
              <FlexItem>
                <DashboardTotals
                  title={'Cost of manual automation'}
                  result={manual_automation_cost.value ? manual_automation_cost.value.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) : ''}
                  percentage={manual_automation_cost.index}
                />
              </FlexItem>
              <FlexItem>
                <DashboardTotals
                  title={'Cost of automated execution'}
                  result={automated_execution_cost.value ? automated_execution_cost.value.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) : ''}
                  percentage={automated_execution_cost.index}
                />
              </FlexItem>
              <FlexItem>
                <DashboardTotals
                  title={'Total savings'}
                  result={total_savings.value ? total_savings.value.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) : ''}
                  percentage={total_savings.index}
                />
              </FlexItem>
            </Flex>
          </Flex>
          <BaseTable
            pagination={{ onPageChange: handlePageChange, onPerPageChange: handlePerPageChange, totalItems: reportsList.count }}
            data={reportsList.reports}
            sort={{ onSortChange: handleSort }}
            columns={columns}
            loading={loadingReports}
          ></BaseTable>
        </CardBody>
      </Card>
    </>
  );
};
