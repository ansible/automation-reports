import React from "react";
import { Chart, ChartAxis, ChartBar, ChartGroup, ChartTooltip, ChartVoronoiContainer } from '@patternfly/react-charts/victory';
import { ChartItem } from "@app/Types/ReportDetailsType";
import '../styles/chart.scss';

export const BarChart: React.FunctionComponent<{data: ChartItem[], maxValue: number, range?: string}> = (props) => {
  const maxChartValue = (value) => {
    if (isNaN(value) || value < 10) {
      return 10;
    }
    const k = Math.floor(Math.log10(value));
    return Math.floor((value + 10 ** k) / 10 ** k) * 10 ** k;
  }

  const generateTicks = (maxValue: number) => {
    const numTicks = 10;
    if (maxValue < 10) {
      return Array.from({length: numTicks}, (_, i) => i + 1);
    }
    const step = Math.ceil(maxValue / numTicks);
    const ticks: number[] = [];
    for (let i = step; i <= maxValue; i += step) {
      ticks.push(i);
    }
    return ticks;
  };

  const roundedMaxValue = maxChartValue(props.maxValue);
  const tickValues = generateTicks(roundedMaxValue);
  
  return (
    <>
      <div className={`chart-wrap ${props.data.length === 0 && 'no-data'}`}>
        <Chart
          ariaDesc="Average number of pets"
          ariaTitle="Bar chart example"
          containerComponent={
            <ChartVoronoiContainer
              labels={({ datum }) => `${datum.x}: ${datum.y}`}
              constrainToVisibleArea
              labelComponent={
                <ChartTooltip
                  style={{fontSize: 10}}
                />
              }
            />
          }
          domainPadding={{ x: [30, 25] }}
          legendData={[{ name: 'items' }]}
          legendOrientation="vertical"
          legendPosition="right"
          name="chart4"
          padding={{
            bottom: props.range === "hour" || props.data.length > 12 ? 36 : 24,
            left: 50,
            right: 24,
            top: 24
          }}
        >  
          <ChartAxis 
            style={{
              tickLabels: {
                fontSize: 6,
                angle: props.range === "hour" || props.data.length > 12 ? -25 : 0,
                textAnchor: 'end'
              }
            }}
          />
          <ChartAxis
            dependentAxis
            tickValues={tickValues}
            style={{tickLabels: { fontSize: 10 }}}
          />
          {props.data.length > 0 &&
            <ChartGroup>
              <ChartBar data={props.data} />
            </ChartGroup>
          }
        </Chart>
      </div>
    </>
  )
}