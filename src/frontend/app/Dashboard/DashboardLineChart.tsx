import React from 'react';
import { Card, CardBody, CardTitle } from '@patternfly/react-core';

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
import { formatNumber, generateChartData } from '@app/Utils';
import { AnimatePropTypeInterface } from 'victory-core';
import { DashboardTotals } from '@app/Dashboard/DashboardTotals';
import { useTranslation } from 'react-i18next';

export const DashboardLineChart: React.FunctionComponent<DashboardChartProps> = (props: DashboardChartProps) => {
  const { t } = useTranslation();
  const chartData = generateChartData(props.chartData);
  const [useAnimation, setUseAnimation] = React.useState<boolean | AnimatePropTypeInterface>(false);
  React.useEffect(() => {
    setUseAnimation({ onLoad: { duration: 1 }, duration: 500 });
  }, [props.chartData]);
  return (
    <>
      <style>
        {`
          .no-data {
            opacity: 0.6;
          }
        `}
      </style>
      <Card style={{ height: 'inherit' }}>
        <CardTitle>
          <DashboardTotals
            title={t('Number of times jobs were run')} result={props.value}
            tooltip={t('This is the total number of individual job executions.')}
            infoIcon={true}
          />
        </CardTitle>
        <CardBody style={{ width: '100%' }}>
          <div className={`pf-v6-u-h-initial pf-v6-u-w-100 jobs-chart ${chartData.items.length === 0 && 'no-data'}`}>
            <Chart
              height={250}
              ariaDesc={t('Number of times jobs were run')}
              ariaTitle={t('Number of times jobs were run')}
              minDomain={{ y: 0 }}
              maxDomain={{ y: chartData.maxValue }}
              domain={{ x: [0, chartData.items.length + 1] }}
              containerComponent={
                <ChartVoronoiContainer
                  labels={({ datum }) => `${formatNumber(datum?.y)}`}
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
                tickFormat={(n) => formatNumber(n)}
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
