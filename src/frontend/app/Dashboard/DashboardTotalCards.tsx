import React from 'react';
import { Grid, GridItem } from '@patternfly/react-core';
import { Card, CardBody } from '@patternfly/react-core';
import { DashboardTotals } from './DashboardTotals';
import '../styles/dashboard-totals.scss';
import { ReportDetail } from '@app/Types';

export const DashboardTotalCards: React.FunctionComponent<{ data: ReportDetail }> = (props: { data: ReportDetail }) => {
  return (
    <>
      <Grid hasGutter>
        <GridItem className="pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-lg">
          <Card className="card">
            <CardBody>
              <DashboardTotals
                title={'Total number of successful jobs'}
                result={props?.data?.total_number_of_successful_jobs?.value}
                percentage={props?.data?.total_number_of_successful_jobs?.index}
              />
            </CardBody>
          </Card>
        </GridItem>
        <GridItem className="pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-lg">
          <Card style={{ height: '100%' }}>
            <CardBody>
              <DashboardTotals
                title={'Total number of failed jobs'}
                result={props?.data?.total_number_of_failed_jobs?.value}
                percentage={props?.data?.total_number_of_failed_jobs?.index}
              />
            </CardBody>
          </Card>
        </GridItem>
        <GridItem className="pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-lg">
          <Card style={{ height: '100%' }}>
            <CardBody>
              <DashboardTotals
                title={'Total number of unique hosts automated'}
                result={props?.data?.total_number_of_unique_hosts?.value}
                percentage={props?.data?.total_number_of_unique_hosts?.index}
              />
            </CardBody>
          </Card>
        </GridItem>
        <GridItem className="pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-lg">
          <Card style={{ height: '100%' }}>
            <CardBody>
              <DashboardTotals
                title={'Total hours of automation'}
                result={
                  props?.data?.total_hours_of_automation?.value ? props.data.total_hours_of_automation.value + 'h' : ''
                }
                percentage={props?.data?.total_hours_of_automation?.index}
              />
            </CardBody>
          </Card>
        </GridItem>
      </Grid>
    </>
  );
};
