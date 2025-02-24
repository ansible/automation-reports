import * as React from 'react';
import { useRef } from 'react';
import { Filters, Header } from '@app/Components';

import '@patternfly/react-styles/css/utilities/Spacing/spacing.css';
import '@patternfly/react-styles/css/utilities/Sizing/sizing.css';
import '@patternfly/react-styles/css/utilities/Text/text.css';
import '@patternfly/react-styles/css/utilities/Flex/flex.css';
import { Grid, GridItem, Spinner } from '@patternfly/react-core';
import { ParamsContext } from '../Store/paramsContext';

import { RestService } from '@app/Services';
import { deepClone } from '@app/Utils';
import { DashboardTopTableColumn, ReportDetail, TableResponse, TableResult, UrlParams } from '@app/Types';
import { useAppSelector } from '@app/hooks';
import { filterRetrieveError } from '@app/Store';
import ErrorState from '@patternfly/react-component-groups/dist/dynamic/ErrorState';
import {
  DashboardBarChart,
  DashboardLineChart,
  DashboardTable,
  DashboardTopTable,
  DashboardTotalCards,
} from '@app/Dashboard';

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
  const prevParams: React.RefObject<UrlParams> = useRef({} as UrlParams);

  const handelError = (error: unknown) => {
    if (error?.['name'] !== 'CanceledError') {
      setLoadDataError(true);
    }
  };

  const fetchServerReportDetails = async (signal: AbortSignal) => {
    const queryParams = deepClone(params);
    delete queryParams['page'];
    delete queryParams['page_size'];
    delete queryParams['ordering'];
    let response: ReportDetail;
    try {
      response = await RestService.fetchReportDetails(signal, queryParams);
      setDetailData(response);
    } catch (e) {
      handelError(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchServerTableData = async (
    signal: AbortSignal | undefined = undefined,
    fetchDetails: boolean = true,
    useLoader: boolean = true,
  ) => {
    if (!signal) {
      const ctrl = new AbortController();
      signal = ctrl.signal;
    }
    if ((!params.date_range || params.date_range === 'custom') && (!params?.start_date || !params?.end_date)) {
      return;
    }

    if (params.date_range === 'custom' && params.start_date && params.end_date && params.start_date > params.end_date) {
      return;
    }

    if (useLoader) {
      setLoading(true);
    }
    const queryParams = deepClone(params);
    let tableResponse: TableResponse;
    try {
      tableResponse = await RestService.fetchReports(signal, queryParams);
      setTableData(tableResponse);
    } catch (e) {
      handelError(e);
    } finally {
      setTableLoading(false);
      if (!fetchDetails) {
        setLoading(false);
      }
    }
    if (fetchDetails) {
      await fetchServerReportDetails(signal);
    }
  };

  React.useEffect(() => {
    const controller = new AbortController();
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
    fetchServerTableData(controller.signal, fetchDetail).then();
    prevParams.current = params;
    return () => {
      controller.abort();
    };
  }, [params]);

  const costChanged = (type: string, value: number) => {
    setTableLoading(true);
    RestService.updateCosts({ type: type, value: value })
      .then(() => {
        fetchServerTableData(undefined, true, false).then();
      })
      .catch((e) => {
        handelError(e);
      });
  };

  const onItemEdit = (value: number, item: TableResult) => {
    setTableLoading(true);
    RestService.updateTemplate(item.job_template_id, value)
      .then(() => {
        fetchServerTableData(undefined, true, false).then();
      })
      .catch((e) => {
        handelError(e);
      });
  };

  const topProjectColumns: DashboardTopTableColumn[] = [
    {
      name: 'project_name',
      title: 'Project name',
    },
    {
      name: 'count',
      title: 'Total number of running jobs',
    },
  ];

  const topUsersColumns: DashboardTopTableColumn[] = [
    {
      name: 'user_name',
      title: 'User name',
    },
    {
      name: 'count',
      title: 'Total number of running jobs',
    },
  ];

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
            ></DashboardTable>
          </div>
        </div>
      )}
    </div>
  );
};

export { Dashboard };
