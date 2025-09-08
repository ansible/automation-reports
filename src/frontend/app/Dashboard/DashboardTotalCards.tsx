import React from 'react';
import { Grid, GridItem } from '@patternfly/react-core';
import { Card, CardBody } from '@patternfly/react-core';
import { ReportDetail } from '@app/Types';
import { formatNumber } from '@app/Utils';
import { DashboardTotals } from '@app/Dashboard/DashboardTotals';

export const DashboardTotalCards: React.FunctionComponent<{ data: ReportDetail }> = (props: { data: ReportDetail }) => {
  return (
    <>
      <Grid hasGutter>
        <GridItem className="pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-lg">
          <Card className="card">
            <CardBody>
              <DashboardTotals
                title={'Total number of successful jobs'}
                tooltip={'This indicates the number of automation jobs that were completed successfully.'}
                infoIcon={true}
                result={props?.data?.total_number_of_successful_jobs?.value}
                url={{
                  url: props?.data?.related_links?.successful_jobs,
                  title: 'See all successful jobs in AAP',
                }}
              />
            </CardBody>
          </Card>
        </GridItem>
        <GridItem className="pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-lg">
          <Card style={{ height: '100%' }}>
            <CardBody>
              <DashboardTotals
                title={'Total number of failed jobs'}
                tooltip={'This shows the number of automation jobs that encountered errors. Analyzing these failures can help improve automation throughput, reduce errors, and improve efficiency.'}
                infoIcon={true}
                result={props?.data?.total_number_of_failed_jobs?.value}
                url={{
                  url: props?.data?.related_links?.failed_jobs,
                  title: 'See all failed jobs in AAP',
                }}
              />
            </CardBody>
          </Card>
        </GridItem>
        <GridItem className="pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-lg">
          <Card style={{ height: '100%' }}>
            <CardBody>
              <DashboardTotals
                title={'Total number of unique hosts automated'}
                tooltip={'This is the number of Controller inventory records you have automated.'}
                infoIcon={true}
                result={props?.data?.total_number_of_unique_hosts?.value}
              />
            </CardBody>
          </Card>
        </GridItem>
        <GridItem className="pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-lg">
          <Card style={{ height: '100%' }}>
            <CardBody>
              <DashboardTotals
                title={'Total hours of automation'}
                tooltip={'This represents the cumulative time that Ansible Automation Platform spent jobs executed.'}
                infoIcon={true}
                result={
                  props?.data?.total_hours_of_automation?.value || props?.data?.total_hours_of_automation?.value === 0
                    ? formatNumber(props.data.total_hours_of_automation.value, 2) + 'h'
                    : ''
                }
              />
            </CardBody>
          </Card>
        </GridItem>
      </Grid>
    </>
  );
};
