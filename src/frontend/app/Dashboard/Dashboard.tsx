import * as React from 'react';
import { Filters, Header } from '@app/Components';
import '@patternfly/react-styles/css/utilities/Spacing/spacing.css';
import '@patternfly/react-styles/css/utilities/Sizing/sizing.css';
import '@patternfly/react-styles/css/utilities/Text/text.css';
import '@patternfly/react-styles/css/utilities/Flex/flex.css';
import { Grid, GridItem, Spinner } from '@patternfly/react-core';
import { ParamsContext } from '../Store/paramsContext';
import { RestService } from '@app/Services';
import { deepClone } from '@app/Utils';
import { columnProps, ReportDetail, TableResponse, TableResult, UrlParams } from '@app/Types';
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

const refreshInterval: string = process.env.DATA_REFRESH_INTERVAL_SECONDS
  ? process.env.DATA_REFRESH_INTERVAL_SECONDS
  : '60';

const Dashboard: React.FunctionComponent = () => {
  const context = React.useContext(ParamsContext);
  if (!context) {
    throw new Error('Filters must be used within a ParamsProvider');
  }
  const { params } = context;
  const filterError = useAppSelector(filterRetrieveError);
  const [tableData, setTableData] = React.useState<TableResponse>({ count: 0, results: [] } as TableResponse);
  const [detailData, setDetailData] = React.useState<ReportDetail>({} as ReportDetail);
  const [loadDataError, setLoadDataError] = React.useState<boolean>(false);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [tableLoading, setTableLoading] = React.useState<boolean>(true);
  const prevParams: React.RefObject<UrlParams> = React.useRef({} as UrlParams);

  const hourly_manual_costs = useAppSelector(manualCostAutomation);
  const hourly_automated_process_costs = useAppSelector(automatedProcessCost);
  const interval = React.useRef<number | undefined>(undefined);

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
    const queryParams = deepClone(params) as object;
    delete queryParams['page'];
    delete queryParams['page_size'];
    delete queryParams['ordering'];
    let response: ReportDetail;

    RestService.fetchReportDetails(signal, queryParams)
      .then((response) => {
        setDetailData(response);
        afterDataRetrieve();
        setLoading(false);
      })
      .catch((e) => {
        handelError(e);
      });
  };

  const fetchServerTableData = (fetchDetails: boolean = true, useLoader: boolean = true) => {
    if (interval.current) {
      clearTimeout();

      detailController.current = new AbortController();
    }
    if (!controller.current) {
      controller.current = new AbortController();
    }

    if ((!params.date_range || params.date_range === 'custom') && (!params?.start_date || !params?.end_date)) {
      return;
    }

    if (params.date_range === 'custom' && params.start_date && params.end_date && params.start_date > params.end_date) {
      return;
    }

    if (useLoader) {
      if (fetchDetails) {
        setLoading(true);
      } else {
        setTableLoading(true);
      }
    }
    const queryParams = deepClone(params) as object;
    let tableResponse: TableResponse;
    RestService.fetchReports(controller.current.signal, queryParams)
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
    clearTimeout();
    controller.current = new AbortController();
    detailController.current = new AbortController();
    let fetchDetail = false;
    for (const [key, value] of Object.entries(params)) {
      if (!key || key === 'page' || key === 'page_size' || key === 'ordering') {
        continue;
      }
      if (prevParams.current?.[key] !== value) {
        fetchDetail = true;
        break;
      }
    }
    fetchServerTableData(fetchDetail);
    prevParams.current = params;
    return () => {
      controller.current?.abort();
      detailController.current?.abort();
    };
  }, [params]);

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

  const onItemEdit = (value: number | string, item: TableResult) => {
    const val = typeof value === 'string' ? parseFloat(value) : value;
    if (val === item.manual_time) {
      afterDataRetrieve();
      return;
    }
    clearTimeout();
    setLoading(true);
    RestService.updateTemplate(item.job_template_id, val)
      .then(() => {
        fetchServerTableData(true, false);
      })
      .catch((e) => {
        handelError(e);
      });
  };

  const topProjectColumns: columnProps[] = [
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

  const topUsersColumns: columnProps[] = [
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
          <Filters></Filters>
          <div>
            <Grid hasGutter>
              <GridItem className="pf-m-12-col pf-m-8-col-on-2xl grid-gap">
                <DashboardTotalCards data={detailData}></DashboardTotalCards>
                <Grid hasGutter>
                  <GridItem className="pf-m-12-col pf-m-6-col-on-md" style={{ height: '100%' }}>
                    <DashboardLineChart
                      value={detailData?.total_number_of_job_runs?.value}
                      index={detailData?.total_number_of_job_runs?.index}
                      chartData={detailData.job_chart}
                      loading={loading}
                    ></DashboardLineChart>
                  </GridItem>
                  <GridItem className="pf-m-12-col pf-m-6-col-on-md" style={{ height: '100%' }}>
                    <DashboardBarChart
                      value={detailData?.total_number_of_host_job_runs?.value}
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
              onItemEdit={onItemEdit}
              loading={tableLoading}
              onInputFocus={onInputFocus}
            ></DashboardTable>
          </div>
        </div>
      )}
    </div>
  );
};

export { Dashboard };
