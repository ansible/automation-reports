import React from 'react';
import { Card, CardBody, CardTitle } from '@patternfly/react-core';

import { DashboardChartProps } from '@app/Types';
import { formatNumber, generateChartData } from '@app/Utils';
import {
  Chart,
  ChartAxis,
  ChartBar,
  ChartGroup,
  ChartTooltip,
  ChartVoronoiContainer,
} from '@patternfly/react-charts/victory';
import { AnimatePropTypeInterface } from 'victory-core';
import { DashboardTotals } from '@app/Dashboard/DashboardTotals';

export const DashboardBarChart: React.FunctionComponent<DashboardChartProps> = (props: DashboardChartProps) => {
  const chartData = generateChartData(props.chartData);
  const [useAnimation, setUseAnimation] = React.useState<boolean | AnimatePropTypeInterface>(false);

  React.useEffect(() => {
    setUseAnimation({ onLoad: { duration: 1 }, duration: 500 });
  }, [props.chartData]);

  return (
    <>
      <Card style={{ height: 'inherit' }}>
        <CardTitle>
          <DashboardTotals title={'Number of hosts jobs are running on'} result={props.value} />
        </CardTitle>
        <CardBody>
          <div className={`chart-wrap host-chart ${chartData.items.length === 0 && 'no-data'}`}>
            <Chart
              height={250}
              ariaDesc="Number of hosts jobs are running on"
              ariaTitle="Number of hosts jobs are running on"
              containerComponent={
                <ChartVoronoiContainer
                  labels={({ datum }) => `${formatNumber(datum?.y)}`}
                  constrainToVisibleArea
                  labelComponent={<ChartTooltip style={{ fontSize: 6 }} />}
                />
              }
              domain={{ x: [0, chartData.items.length + 1] }}
              name="numberOfHostsChart"
              padding={{
                bottom:
                  chartData.range === 'hour' || chartData.range === 'month' || chartData.items.length > 11 ? 36 : 24,
                left: 50,
                right: 24,
                top: 24,
              }}
            >
              <ChartAxis
                style={{
                  tickLabels: {
                    fontSize: props.loading ? 0 : 6,
                    angle: chartData.items.length > 11 ? -45 : 0,
                    verticalAnchor: 'middle',
                  },
                }}
              />
              <ChartAxis
                tickValues={chartData.tickValues}
                dependentAxis
                style={{ tickLabels: { fontSize: 6 } }}
                tickFormat={(n) => formatNumber(n)}
              />
              {!props.loading && chartData.items.length > 0 && (
                <ChartGroup>
                  <ChartBar
                    cornerRadius={{ bottomLeft: 0, bottomRight: 0, topLeft: 2, topRight: 2 }}
                    barWidth={(x) => {
                      return x?.data?.length && x.data.length <= 6 ? 50 : 10;
                    }}
                    alignment={'middle'}
                    data={chartData.items}
                    animate={useAnimation}
                  />
                </ChartGroup>
              )}
            </Chart>
          </div>
        </CardBody>
      </Card>
    </>
  );
};
