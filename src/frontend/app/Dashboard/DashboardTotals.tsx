import React from 'react';
import { Icon, Tooltip } from '@patternfly/react-core';
import { ArrowCircleDownIcon, ArrowCircleUpIcon, MinusIcon, OutlinedQuestionCircleIcon } from '@patternfly/react-icons';
import '../styles/dashboard-totals.scss';

type CardProps = {
  title: string | '';
  result: number | string | null;
  percentage?: number | null;
  invert?: boolean;
  tooltip?: string;
};

export const DashboardTotals: React.FunctionComponent<CardProps> = (props) => {
  const percentageClass: string[] = ['percentage', 'fw-500'];
  if (!props.percentage) {
    percentageClass.push('grey');
  } else if ((props.percentage > 0 && !props.invert) || (props.percentage < 0 && props.invert)) {
    percentageClass.push('green');
  } else {
    percentageClass.push('red');
  }

  const percentage =
    props.percentage !== null && props.percentage !== undefined ? (
      <span>
        {props.percentage > 0 && (
          <Icon size="lg" className={'arrow-up' + (props?.invert ? ' invert' : '')}>
            <ArrowCircleUpIcon />
          </Icon>
        )}
        {props.percentage < 0 && (
          <Icon size="lg" className={'arrow-down' + (props?.invert ? ' invert' : '')}>
            <ArrowCircleDownIcon />
          </Icon>
        )}
        {props.percentage === 0 && (
          <Icon size="lg" className={'minus-circle'}>
            <MinusIcon />
          </Icon>
        )}
        {
          <span className={percentageClass.join(' ')}>
            ({props.percentage > 0 && <span>+</span>}
            {props.percentage}%)
          </span>
        }
      </span>
    ) : (
      <Icon size="lg" className={'minus-circle'}>
        <MinusIcon />
      </Icon>
    );

  return (
    <>
      <div className="content">
        <div>
          <span className="pf-v6-u-font-size-md">
            {props.title}
            {props.tooltip && (
              <Tooltip content={props.tooltip}>
                <Icon size="md" className="pf-v6-u-ml-sm">
                  <OutlinedQuestionCircleIcon />
                </Icon>
              </Tooltip>
            )}
          </span>
        </div>
        <div className="value">
          <span className="pf-v6-u-font-size-4xl fw-500 result">{props.result?.toLocaleString('en-US')}</span>
          {percentage}
        </div>
      </div>
    </>
  );
};
