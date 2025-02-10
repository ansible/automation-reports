import * as React from 'react';
import { Filters, Header } from '@app/Components';

import '@patternfly/react-styles/css/utilities/Spacing/spacing.css';
import '@patternfly/react-styles/css/utilities/Sizing/sizing.css';
import '@patternfly/react-styles/css/utilities/Text/text.css';
import '@patternfly/react-styles/css/utilities/Flex/flex.css';
import { Grid, GridItem } from '@patternfly/react-core';
import { DashboardLineChart } from './DashboardLineChart';
import { DashboardBarChart } from './DashboardBarChart';
import { DashboardTopProjectsTable } from './DashboardTopProjectsTable';
import { DashboardTopUsersTable } from './DashboardTopUsersTable';
import { DashboardTable } from './DashboardTable';
import { DashboardTotalCards } from './DashboardTotalCards';
import { ParamsContext } from "../Store/paramsContext";
import { useAppDispatch } from '@app/hooks';
import { fetchReportDetails } from '@app/Store/';

const Dashboard: React.FunctionComponent = () => {
  const dispatch = useAppDispatch();

  const context = React.useContext(ParamsContext);
  if (!context) {
    throw new Error('Filters must be used within a ParamsProvider');
  }
  const {params} = context;

  React.useEffect(()=> {
    fetchServerData();
  }, [
    dispatch,
    params.job_template,
    params.date_range,
    params.start_date,
    params.end_date,
    params.organization
  ]);

  const fetchServerData = async () => {
    let queryParams = JSON.parse(JSON.stringify(params))
    delete (queryParams as { [key: string]: any })["page"];
    delete (queryParams as { [key: string]: any })["page_size"];
    await dispatch(fetchReportDetails(queryParams))
  }

  return (
    <div>
    <Header title={'Automation Savings Service'} subtitle={'Discover the significant cost and time savings achieved by automating Ansible jobs with the Ansible Automation Platform. Explore how automation reduces manual effort, enhances efficiency, and optimizes IT operations across your organization.'}></Header>

      <div className={'main-layout'}>
        <Filters></Filters>
        <div>
          <Grid hasGutter>
            <GridItem className='pf-m-12-col pf-m-8-col-on-2xl grid-gap'>
              <DashboardTotalCards></DashboardTotalCards>
              <Grid hasGutter>
                <GridItem className='pf-m-12-col pf-m-6-col-on-md' style={{ height: '100%' }}>
                  <DashboardLineChart></DashboardLineChart>
                </GridItem>
                <GridItem className='pf-m-12-col pf-m-6-col-on-md' style={{ height: '100%' }}>
                  <DashboardBarChart></DashboardBarChart>
                </GridItem>
              </Grid>
            </GridItem>

            <GridItem className='pf-m-12-col-on-lg pf-m-4-col-on-2xl'>
              <Grid hasGutter style={{ height: '100%' }}>
                <GridItem className='pf-m-12-col pf-m-6-col-on-md pf-m-12-col-on-2xl' style={{ height: '100%' }}>
                  <div style={{ height: '100%' }}>
                    <DashboardTopProjectsTable></DashboardTopProjectsTable>
                  </div>
                </GridItem>
                <GridItem className='pf-m-12-col pf-m-6-col-on-md pf-m-12-col-on-2xl' style={{ height: '100%' }}>
                  <div style={{ height: '100%' }}>
                    <DashboardTopUsersTable></DashboardTopUsersTable>
                  </div>
                </GridItem>
              </Grid>
            </GridItem>
          </Grid>
        </div>
        <div className='pf-v6-u-mt-xl'>
          <DashboardTable></DashboardTable>
        </div>
      </div>
  </div>
  )
};

export { Dashboard };
