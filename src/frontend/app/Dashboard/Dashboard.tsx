import * as React from 'react';
import { Filters, Header } from '@app/Components';
import '@patternfly/react-styles/css/utilities/Spacing/spacing.css';
import '@patternfly/react-styles/css/utilities/Sizing/sizing.css';
import '@patternfly/react-styles/css/utilities/Text/text.css';
import '@patternfly/react-styles/css/utilities/Flex/flex.css';
import { Flex, FlexItem, Grid, GridItem, Spinner, Toolbar, ToolbarItem } from '@patternfly/react-core';
import { RestService } from '@app/Services';
import { deepClone } from '@app/Utils';
import {
  ColumnProps,
  OrderingParams,
  PaginationParams,
  ReportDetail,
  RequestFilter,
  TableResponse,
  TableResult,
  UrlParams,
} from '@app/Types';
import { useAppSelector } from '@app/hooks';
import { automatedProcessCost, filterRetrieveError, manualCostAutomation } from '@app/Store';
import ErrorState from '@patternfly/react-component-groups/dist/dynamic/ErrorState';
import {
  DashboardBarChart,
  DashboardLineChart,
  DashboardTable,
  DashboardTopTable,
  DashboardTotalCards,
} from '@app/Dashboard';

import { CurrencySelector } from '@app/Components';

const refreshInterval: string = process.env.DATA_REFRESH_INTERVAL_SECONDS
  ? process.env.DATA_REFRESH_INTERVAL_SECONDS
  : '60';

const Dashboard: React.FunctionComponent = () => {
  const filterError = useAppSelector(filterRetrieveError);
  const [tableData, setTableData] = React.useState<TableResponse>({ count: 0, results: [] } as TableResponse);
  const [detailData, setDetailData] = React.useState<ReportDetail>({} as ReportDetail);
  const [loadDataError, setLoadDataError] = React.useState<boolean>(false);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [tableLoading, setTableLoading] = React.useState<boolean>(true);
  const [requestParams, setRequestParams] = React.useState<RequestFilter>();
  const [paginationParams, setPaginationParams] = React.useState<PaginationParams>({
    page: 1,
    page_size: 10,
  } as PaginationParams);
  const [ordering, setOrdering] = React.useState<string>('name');
  const hourly_manual_costs = useAppSelector(manualCostAutomation);
  const hourly_automated_process_costs = useAppSelector(automatedProcessCost);
  const interval = React.useRef<number | undefined>(undefined);
  const requestParamsData = React.useRef<RequestFilter>(requestParams as RequestFilter);

  const controller = React.useRef<AbortController | undefined>(undefined);
  const detailController = React.useRef<AbortController | undefined>(undefined);

  const handelError = (error: unknown) => {
    if (error?.['name'] !== 'CanceledError') {
      setLoadDataError(true);
      setLoading(false);
      setTableLoading(false);
    }
  };

  const fetchServerReportDetails = (signal: AbortSignal) => {
    if (!requestParams) {
      return;
    }
    RestService.fetchReportDetails(signal, requestParams)
      .then((response) => {
        setDetailData(response);
        afterDataRetrieve();
        setLoading(false);
      })
      .catch((e) => {
        handelError(e);
      });
  };

  const fetchServerTableData = (fetchDetails: boolean, useLoader: boolean = true) => {
    if (interval.current) {
      clearTimeout();

      detailController.current = new AbortController();
    }
    if (!controller.current) {
      controller.current = new AbortController();
    }

    if (useLoader) {
      if (fetchDetails) {
        setLoading(true);
      } else {
        setTableLoading(true);
      }
    }

    RestService.fetchReports(controller.current.signal, {
      ...requestParams,
      ...paginationParams,
      ...{ ordering: ordering },
    } as UrlParams)
      .then((tableResponse) => {
        setTableData(tableResponse);
        setTableLoading(false);
        if (fetchDetails) {
          if (!detailController.current) {
            detailController.current = new AbortController();
          }
          fetchServerReportDetails(detailController.current.signal);
        } else {
          afterDataRetrieve();
          setLoading(false);
        }
      })
      .catch((e) => {
        handelError(e);
      });
  };

  const afterDataRetrieve = () => {
    interval.current = window.setTimeout(
      () => {
        fetchServerTableData(true, false);
      },
      parseInt(refreshInterval) * 1000,
    );
  };

  const clearTimeout = () => {
    controller.current?.abort();
    controller.current = undefined;
    detailController.current?.abort();
    detailController.current = undefined;
    if (interval.current) {
      window.clearTimeout(interval.current);
      interval.current = undefined;
    }
  };

  React.useEffect(() => {
    if (!requestParams) {
      return;
    }
    clearTimeout();
    controller.current = new AbortController();
    detailController.current = new AbortController();
    const fetchDetails = requestParamsData.current !== requestParams;
    fetchServerTableData(fetchDetails);
    requestParamsData.current = requestParams;
    return () => {
      controller.current?.abort();
      detailController.current?.abort();
    };
  }, [requestParams, paginationParams, ordering]);

  const costChanged = (type: string, value: number) => {
    const oldValue = type === 'manual' ? hourly_manual_costs : hourly_automated_process_costs;
    if (oldValue !== value) {
      clearTimeout();
      setLoading(true);
      RestService.updateCosts({ type: type, value: value })
        .then(() => {
          fetchServerTableData(true, false);
        })
        .catch((e) => {
          handelError(e);
        });
    } else {
      afterDataRetrieve();
    }
  };

  const onItemEdit = (newValue: TableResult, oldValue: TableResult) => {
    let manually_minutes = newValue.time_taken_manually_execute_minutes;
    let automation_minutes = newValue.time_taken_create_automation_minutes;

    manually_minutes = typeof manually_minutes === 'string' ? parseFloat(manually_minutes) : manually_minutes;

    automation_minutes = typeof automation_minutes === 'string' ? parseFloat(automation_minutes) : automation_minutes;

    if (
      oldValue.time_taken_manually_execute_minutes === manually_minutes &&
      oldValue.time_taken_create_automation_minutes === automation_minutes
    ) {
      afterDataRetrieve();
      return;
    }
    clearTimeout();
    setLoading(true);
    const newItem = deepClone(newValue) as TableResult;
    newItem.time_taken_manually_execute_minutes = manually_minutes;
    newItem.time_taken_create_automation_minutes = automation_minutes;
    RestService.updateTemplate(newItem)
      .then(() => {
        fetchServerTableData(true, false);
      })
      .catch((e) => {
        handelError(e);
      });
  };

  const filtersChange = (requestFilter: RequestFilter) => {
    setRequestParams(requestFilter);
  };

  const onPaginationChange = (pagination: PaginationParams) => {
    setPaginationParams(pagination);
  };

  const onSortChange = (ordering: string) => {
    setOrdering(ordering);
  };

  const topProjectColumns: ColumnProps[] = [
    {
      name: 'project_name',
      title: 'Project name',
    },
    {
      name: 'count',
      title: 'Total number of running jobs',
      type: 'number',
    },
  ];

  const topUsersColumns: ColumnProps[] = [
    {
      name: 'user_name',
      title: 'User name',
    },
    {
      name: 'count',
      title: 'Total number of running jobs',
      type: 'number',
    },
  ];

  const onInputFocus = () => {
    clearTimeout();
  };

  const exportToCsv = () => {
    setTableLoading(true);
    RestService.exportToCSV({ ...requestParams, ...{ ordering: ordering } } as RequestFilter & OrderingParams)
      .then(() => {
        setTableLoading(false);
      })
      .catch((e) => {
        handelError(e);
      });
  };

  return (
    <div>
      <Header
        title={'Automation Savings Service'}
        subtitle={
          'Discover the significant cost and time savings achieved by automating Ansible jobs with the Ansible Automation Platform. Explore how automation reduces manual effort, enhances efficiency, and optimizes IT operations across your organization.'
        }
      ></Header>
      {(loadDataError || filterError) && (
        <div className={'error'}>
          <ErrorState
            titleText="Something went wrong"
            bodyText="Please contact your system administrator."
            customFooter="&nbsp;"
            headingLevel={'h1'}
            variant={'full'}
          />
        </div>
      )}
      {!loadDataError && !filterError && (
        <div className={'main-layout'}>
          {loading && (
            <div className={'loader'}>
              <Spinner className={'spinner'} diameter="80px" aria-label="Loader" />
            </div>
          )}
          <Flex>
            <FlexItem>
              <Filters onChange={filtersChange}></Filters>
            </FlexItem>
            <FlexItem align={{ default: 'alignLeft', '2xl': 'alignRight' }}>
              <Toolbar>
                <ToolbarItem>
                  <CurrencySelector></CurrencySelector>
                </ToolbarItem>
              </Toolbar>
            </FlexItem>
          </Flex>
          <div>
            <Grid hasGutter>
              <GridItem className="pf-m-12-col pf-m-8-col-on-2xl grid-gap">
                <DashboardTotalCards data={detailData}></DashboardTotalCards>
                <Grid hasGutter>
                  <GridItem className="pf-m-12-col pf-m-6-col-on-md" style={{ height: '100%' }}>
                    <DashboardLineChart
                      value={detailData?.total_number_of_job_runs?.value as number}
                      index={detailData?.total_number_of_job_runs?.index}
                      chartData={detailData.job_chart}
                      loading={loading}
                    ></DashboardLineChart>
                  </GridItem>
                  <GridItem className="pf-m-12-col pf-m-6-col-on-md" style={{ height: '100%' }}>
                    <DashboardBarChart
                      value={detailData?.total_number_of_host_job_runs?.value as number}
                      index={detailData?.total_number_of_host_job_runs?.index}
                      chartData={detailData?.host_chart}
                      loading={loading}
                    ></DashboardBarChart>
                  </GridItem>
                </Grid>
              </GridItem>

              <GridItem className="pf-m-12-col-on-lg pf-m-4-col-on-2xl">
                <Grid hasGutter style={{ height: '100%' }}>
                  <GridItem className="pf-m-12-col pf-m-6-col-on-md pf-m-12-col-on-2xl" style={{ height: '100%' }}>
                    <div style={{ height: '100%' }}>
                      <DashboardTopTable
                        title={'Top 5 projects'}
                        columns={topProjectColumns}
                        data={detailData?.projects ? detailData.projects : []}
                      ></DashboardTopTable>
                    </div>
                  </GridItem>
                  <GridItem className="pf-m-12-col pf-m-6-col-on-md pf-m-12-col-on-2xl" style={{ height: '100%' }}>
                    <div style={{ height: '100%' }}>
                      <DashboardTopTable
                        title={'Top 5 users'}
                        columns={topUsersColumns}
                        data={detailData?.users ? detailData.users : []}
                      ></DashboardTopTable>
                    </div>
                  </GridItem>
                </Grid>
              </GridItem>
            </Grid>
          </div>
          <div className="pf-v6-u-mt-xl">
            <DashboardTable
              data={tableData}
              onCostChanged={costChanged}
              totalSaving={detailData?.total_saving}
              costOfAutomatedExecution={detailData.cost_of_automated_execution}
              costOfManualAutomation={detailData.cost_of_manual_automation}
              totalTimeSavings={detailData.total_time_saving}
              onPaginationChange={onPaginationChange}
              onSortChange={onSortChange}
              pagination={paginationParams}
              onItemEdit={onItemEdit}
              loading={tableLoading}
              onInputFocus={onInputFocus}
              onExportCsv={exportToCsv}
            ></DashboardTable>
          </div>
        </div>
      )}
    </div>
  );
};

export { Dashboard };
