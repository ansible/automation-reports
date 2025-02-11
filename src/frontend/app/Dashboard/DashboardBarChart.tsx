import React from 'react';
import { Card, CardBody, CardTitle } from '@patternfly/react-core';
import { DashboardTotals } from './DashboardTotals';
import { DashboardChartProps } from '@app/Types';
import { generateChartData } from '@app/Utils';
import {
  Chart,
  ChartAxis,
  ChartBar,
  ChartGroup,
  ChartTooltip,
  ChartVoronoiContainer,
} from '@patternfly/react-charts/victory';

export const DashboardBarChart: React.FunctionComponent<DashboardChartProps> = (props: DashboardChartProps) => {
  const chartData = generateChartData(props.chartData);

  return (
    <>
      <Card style={{ height: 'inherit' }}>
        <CardTitle>
          <DashboardTotals
            title={'Number of hosts jobs are running on'}
            result={props.value}
            percentage={props.index}
          />
        </CardTitle>
        <CardBody>
          <div className={`chart-wrap ${chartData.items.length === 0 && 'no-data'}`}>
            <Chart
              ariaDesc="Average number of pets"
              ariaTitle="Bar chart example"
              containerComponent={
                <ChartVoronoiContainer
                  labels={({ datum }) => `${datum.x}: ${datum.y}`}
                  constrainToVisibleArea
                  labelComponent={<ChartTooltip style={{ fontSize: 6 }} />}
                />
              }
              domainPadding={{ x: [30, 25] }}
              legendData={[{ name: 'items' }]}
              legendOrientation="vertical"
              legendPosition="right"
              name="chart4"
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
                    fontSize: 6,
                    angle: chartData.items.length > 11 ? -45 : 0,
                    textAnchor: 'end',
                  },
                }}
              />
              <ChartAxis tickValues={chartData.tickValues} dependentAxis style={{ tickLabels: { fontSize: 6 } }} />
              {chartData.items.length > 0 && (
                <ChartGroup>
                  <ChartBar data={chartData.items} />
                </ChartGroup>
              )}
            </Chart>
          </div>
        </CardBody>
      </Card>
    </>
  );
};
