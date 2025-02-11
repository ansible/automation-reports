import React from 'react';
import { Icon } from '@patternfly/react-core';
import { ArrowCircleUpIcon, ArrowCircleDownIcon } from '@patternfly/react-icons';
import '../styles/dashboard-totals.scss';

interface CardProps {
  title: string | '';
  result: number | string | null;
  percentage?: number | null;
}

export const DashboardTotals: React.FunctionComponent<CardProps> = (props) => {
  const percentage =
    props.percentage !== null && props.percentage !== undefined ? (
      <span>
        {props.percentage > 0 ? (
          <Icon size="lg" className="arrow-up">
            <ArrowCircleUpIcon />
          </Icon>
        ) : (
          <Icon size="lg" className="arrow-down">
            <ArrowCircleDownIcon />
          </Icon>
        )}
        <span className={`percentage fw-500 ${props.percentage > 0 ? 'green' : 'red'}`}>
          ({props.percentage > 0 && <span>+</span>}
          {props.percentage}%)
        </span>
      </span>
    ) : (
      <span className="fw-500 pf-v6-u-font-size-4xl"> - </span>
    );

  return (
    <>
      <div className="content">
        <div>
          <span className="pf-v6-u-font-size-md">{props.title}</span>
        </div>
        <div className="value">
          <span className="pf-v6-u-font-size-4xl fw-500 result">{props.result?.toLocaleString('en-US')}</span>
          {percentage}
        </div>
      </div>
    </>
  );
};
