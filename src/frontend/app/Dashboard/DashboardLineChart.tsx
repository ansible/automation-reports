import React from 'react';
import { Card, CardBody, CardTitle } from '@patternfly/react-core';
import { DashboardTotals } from './DashboardTotals';
import { DashboardChartProps } from '@app/Types';
import {
  Chart,
  ChartAxis,
  ChartGroup,
  ChartLine,
  ChartThemeColor,
  ChartTooltip,
  ChartVoronoiContainer,
} from '@patternfly/react-charts/victory';
import { generateChartData } from '@app/Utils';
import '../styles/chart.scss';
import { AnimatePropTypeInterface } from 'victory-core';

export const DashboardLineChart: React.FunctionComponent<DashboardChartProps> = (props: DashboardChartProps) => {
  const chartData = generateChartData(props.chartData);
  const [useAnimation, setUseAnimation] = React.useState<boolean | AnimatePropTypeInterface>(false);
  React.useEffect(() => {
    setUseAnimation({ onLoad: { duration: 1 }, duration: 500 });
  }, [props.chartData]);
  return (
    <>
      <Card style={{ height: 'inherit' }}>
        <CardTitle>
          <DashboardTotals title={'Number of times jobs were run'} result={props.value} percentage={props.index} />
        </CardTitle>
        <CardBody style={{ width: '100%' }}>
          <div className={`chart-wrap ${chartData.items.length === 0 && 'no-data'}`}>
            <Chart
              height={250}
              ariaDesc="Number of times jobs were run"
              ariaTitle="Number of times jobs were run"
              minDomain={{ y: 0 }}
              maxDomain={{ y: chartData.maxValue }}
              domain={{ x: [0, chartData.items.length + 1] }}
              containerComponent={
                <ChartVoronoiContainer
                  labels={({ datum }) => `${datum?.x}: ${datum?.y}`}
                  constrainToVisibleArea
                  labelComponent={<ChartTooltip style={{ fontSize: 6 }} />}
                />
              }
              padding={{
                bottom:
                  chartData.range === 'hour' || chartData.range === 'month' || chartData.items.length > 11 ? 36 : 24,
                left: 50,
                right: 24,
                top: 24,
              }}
              themeColor={ChartThemeColor.blue}
            >
              <ChartAxis
                style={{
                  tickLabels: {
                    fontSize: props.loading ? 0 : 6,
                    angle: chartData.items.length > 11 ? -45 : 0,
                    textAnchor: 'middle',
                  },
                }}
              />

              <ChartAxis
                dependentAxis
                tickValues={chartData.tickValues}
                style={{
                  tickLabels: {
                    fontSize: 6,
                  },
                }}
              />

              {!props.loading && chartData?.items?.length && (
                <ChartGroup>
                  <ChartLine interpolation="monotoneX" data={chartData.items} animate={useAnimation} />
                </ChartGroup>
              )}
            </Chart>
          </div>
        </CardBody>
      </Card>
    </>
  );
};
