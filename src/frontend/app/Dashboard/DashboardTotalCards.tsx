import React from "react";
import { Grid, GridItem } from '@patternfly/react-core';
import { Card, CardBody } from '@patternfly/react-core';
import { DashboardTotals } from "./DashboardTotals";
import { useAppSelector } from "@app/hooks";
import { totalHoursOfAutomation, totalNumberOfFailedJobs, totalNumberOfSuccessfulJobs, totalNumberOfUniqueHosts } from "@app/Store";
import '../styles/dashboard-totals.scss';

export const DashboardTotalCards: React.FunctionComponent = () => {
  const total_num_of_success_jobs = useAppSelector(totalNumberOfSuccessfulJobs) || { value: null, index: null };
  const total_num_of_failed_jobs = useAppSelector(totalNumberOfFailedJobs) || { value: null, index: null };
  const total_num_of_unique_hosts = useAppSelector(totalNumberOfUniqueHosts) || { value: null, index: null };
  const total_hours_of_automation = useAppSelector(totalHoursOfAutomation) || { value: null, index: null };
  return (
    <>
      <Grid hasGutter>
        <GridItem className='pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-lg'>
          <Card className="card">
            <CardBody>
              <DashboardTotals
                title={'Total number of successful jobs'}
                result={total_num_of_success_jobs.value}
                percentage={total_num_of_success_jobs.index}
              />
            </CardBody>
          </Card>
        </GridItem>
        <GridItem className='pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-lg'>
          <Card style={{height: "100%"}}>
            <CardBody>
              <DashboardTotals
                title={'Total number of failed jobs'}
                result={total_num_of_failed_jobs.value}
                percentage={total_num_of_failed_jobs.index}
              />
            </CardBody>
          </Card>
        </GridItem>
        <GridItem className='pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-lg'>
          <Card style={{height: "100%"}}>
            <CardBody>
              <DashboardTotals
                title={'Total number of unique hosts automated'}
                result={total_num_of_unique_hosts.value}
                percentage={total_num_of_unique_hosts.index}
              />
            </CardBody>
          </Card>
        </GridItem>
        <GridItem className='pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-lg'>
          <Card style={{height: "100%"}}>
            <CardBody>
              <DashboardTotals
                title={'Total hours of automation'}
                result={total_hours_of_automation.value ? total_hours_of_automation.value + 'h' : ''}
                percentage={total_hours_of_automation.index}
              />
            </CardBody>
          </Card>
        </GridItem>
      </Grid>
    </>
  )
}