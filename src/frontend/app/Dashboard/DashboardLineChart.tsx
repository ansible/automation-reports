import React from "react";
import { Card, CardBody, CardTitle } from '@patternfly/react-core';
import { DashboardTotals } from "./DashboardTotals";
import { LineChart } from "@app/Components/LineChart";
import { useAppSelector } from "@app/hooks";
import { jobChartData, totalNumberOfJobRuns } from "@app/Store";
import { CHART_RANGES } from "@app/constants";
import moment from "moment";

export const DashboardLineChart: React.FunctionComponent = () => {
  const total_num_of_jobs_run = useAppSelector(totalNumberOfJobRuns) || { value: null, index: null };
  const job_chart_data = useAppSelector(jobChartData) || {items: [], range: null};

  const items = job_chart_data.items.map((point) => {
    let range =  job_chart_data.range ? job_chart_data.range : "";
    
    return ({
      x: moment(point.x).format(CHART_RANGES[range].groupFormat),
      y: point.y
    })
  });
  const maxY = job_chart_data.items.length > 0 ? Math.max(...job_chart_data.items.map(item => item.y)) : 0;
  return (
    <>
      <Card style={{height: 'inherit'}}>
        <CardTitle>
          <DashboardTotals
            title={'Number of times jobs were run'}
            result={total_num_of_jobs_run.value}
            percentage={total_num_of_jobs_run.index}
          />
        </CardTitle>
        <CardBody>
            <LineChart
              data={items}
              maxValue={maxY}
              range={job_chart_data.range ? job_chart_data.range : ""}
            >
            </LineChart>
        </CardBody>
      </Card>
    </>
  )
}