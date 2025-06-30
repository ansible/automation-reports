import React from 'react';
import { Button, Icon, Tooltip } from '@patternfly/react-core';
import { ExternalLinkSquareAltIcon, OutlinedQuestionCircleIcon } from '@patternfly/react-icons';
import '../styles/dashboard-totals.scss';

type urlProps = {
  url?: string;
  title?: string;
};

type CardProps = {
  title: string | '';
  result: number | string | null;
  tooltip?: string;
  url?: urlProps;
};

export const DashboardTotals: React.FunctionComponent<CardProps> = (props) => {
  const link = props?.url && (
    <Button isInline variant="link" icon={<ExternalLinkSquareAltIcon />} iconPosition="end">
      <a href={props.url.url} target={'_blank'} rel="noreferrer">
        {' '}
        {props?.url.title}
      </a>
    </Button>
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
        {link}
        <div className="value">
          <span className="pf-v6-u-font-size-4xl fw-500 result">{props.result?.toLocaleString('en-US')}</span>
        </div>
      </div>
    </>
  );
};
