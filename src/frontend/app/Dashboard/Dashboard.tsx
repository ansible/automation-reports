import * as React from 'react';
import { Filters, Header } from '@app/Components';

import '@patternfly/react-styles/css/utilities/Spacing/spacing.css';
import '@patternfly/react-styles/css/utilities/Sizing/sizing.css';
import '@patternfly/react-styles/css/utilities/Text/text.css';
import '@patternfly/react-styles/css/utilities/Flex/flex.css';
import { Grid, GridItem } from '@patternfly/react-core';
import { DashboardLineChart } from './DashboardLineChart';
import { DashboardBarChart } from './DashboardBarChart';
import { DashboardTable } from './DashboardTable';
import { DashboardTotalCards } from './DashboardTotalCards';
import { ParamsContext } from '../Store/paramsContext';

import { RestService } from '@app/Services';
import { deepClone } from '@app/Utils';
import { DashboardTopTableColumn, ReportDetail, TableResponse, TableResult } from '@app/Types';
import { DashboardTopTable } from '@app/Dashboard/DashboardTopTable';

const Dashboard: React.FunctionComponent = () => {
  const context = React.useContext(ParamsContext);
  if (!context) {
    throw new Error('Filters must be used within a ParamsProvider');
  }
  const { params } = context;

  const [tableData, setTableData] = React.useState<TableResponse>({ count: 0, results: [] } as TableResponse);
  const [detailData, setDetailData] = React.useState<ReportDetail>({} as ReportDetail);
  const [loadDataError, setLoadDataError] = React.useState<boolean>(false);

  const fetchServerReportDetails = async () => {
    const queryParams = deepClone(params);
    delete queryParams['page'];
    delete queryParams['page_size'];
    let response: ReportDetail;
    try {
      response = await RestService.fetchReportDetails(queryParams);
      setDetailData(response);
    } catch {
      setLoadDataError(true);
    }
  };

  const fetchServerTableData = async () => {
    const queryParams = deepClone(params);
    let tableResponse: TableResponse;
    try {
      tableResponse = await RestService.fetchReports(queryParams);
      setTableData(tableResponse);
    } catch {
      setLoadDataError(true);
    }
    await fetchServerReportDetails();
  };

  React.useEffect(() => {
    if ((!params.date_range || params.date_range === 'custom') && (!params?.start_date || !params?.end_date)) {
      return;
    }

    fetchServerTableData().then();
  }, [params]);

  const costChanged = (type: string, value: number) => {
    RestService.updateCosts({ type: type, value: value })
      .then(() => {
        fetchServerTableData().then();
      })
      .catch(() => {
        setLoadDataError(true);
      });
  };

  const onItemEdit = (value: number, item: TableResult) => {
    RestService.updateTemplate(item.job_template_id, value)
      .then(() => {
        fetchServerTableData().then();
      })
      .catch(() => {
        setLoadDataError(true);
      });
  };

  const topProjectColumns: DashboardTopTableColumn[] = [
    {
      name: 'project_name',
      title: 'Project name',
    },
    {
      name: 'count',
      title: 'Total time of running jobs',
    },
  ];

  const topUsersColumns: DashboardTopTableColumn[] = [
    {
      name: 'user_name',
      title: 'User name',
    },
    {
      name: 'count',
      title: 'Total time of running jobs',
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
      {!loadDataError && (
        <div className={'main-layout'}>
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
                    ></DashboardLineChart>
                  </GridItem>
                  <GridItem className="pf-m-12-col pf-m-6-col-on-md" style={{ height: '100%' }}>
                    <DashboardBarChart
                      value={detailData?.total_number_of_host_job_runs?.value}
                      index={detailData?.total_number_of_host_job_runs?.index}
                      chartData={detailData?.host_chart}
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
            ></DashboardTable>
          </div>
        </div>
      )}
    </div>
  );
};

export { Dashboard };
