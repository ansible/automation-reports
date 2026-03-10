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
                title={'Successful jobs'}
                tooltip={
                  'Number of job runs that completed without error in the selected period. Use the ratio between successful and failed jobs to track automation health and reliability over time.'
                }
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
                title={'Failed jobs'}
                tooltip={
                  'Number of job runs that ended in failure in the selected period. Review failed jobs to fix playbooks, credentials, or inventory issues and improve success rates.'
                }
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
                title={'Hosts automated'}
                tooltip={
                  'Number of hosts that executed at least one automation job in the selected period. Indicates how much of your inventory is actively automated and can help with license or capacity planning.'
                }
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
                title={'Hours of automation'}
                tooltip={
                  'Sum of all job runtimes in the selected period. Reflects total automation workload and can inform capacity planning and resource allocation.'
                }
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
