import React from "react";
import { Card, CardBody, CardTitle } from '@patternfly/react-core';
import { DashboardTotals } from "./DashboardTotals";
import { BarChart } from "@app/Components/BarChart";
import { useAppSelector } from "@app/hooks";
import { hostChartData, totalNumberOfHostJobRuns } from "@app/Store";
import { CHART_RANGES } from "@app/constants";
import moment from "moment";

export const DashboardBarChart: React.FunctionComponent = () => {
  const total_num_of_host_jobs_run = useAppSelector(totalNumberOfHostJobRuns) || { value: null, index: null };
  const host_chart_data = useAppSelector(hostChartData) || {items: [], range: null}

  const items = host_chart_data.items.map((point) => {
    let range =  host_chart_data.range ? host_chart_data.range : "";
    return ({
      x: moment(point.x).format(CHART_RANGES[range].groupFormat),
      y: point.y
    })
  });

  const maxY = host_chart_data.items.length > 0 ? Math.max(...host_chart_data.items.map(item => item.y)) : 0;
  
  return (
    <>
      <Card style={{height: 'inherit'}}>
        <CardTitle>
          <DashboardTotals
            title={'Number of hosts jobs are running on'}
            result={total_num_of_host_jobs_run.value}
            percentage={total_num_of_host_jobs_run.index}
          />
        </CardTitle>
        <CardBody>
          <BarChart
            data={items}
            maxValue={maxY}
            range={host_chart_data.range ? host_chart_data.range : ""}
          >
          </BarChart>
        </CardBody>
      </Card>
    </>
  )
};