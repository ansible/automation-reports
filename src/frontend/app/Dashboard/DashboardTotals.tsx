import React from 'react';
import { Button, Flex, FlexItem, Icon, Tooltip } from '@patternfly/react-core';
import { ExternalLinkSquareAltIcon, OutlinedQuestionCircleIcon } from '@patternfly/react-icons';

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
      <Flex direction={{ default: 'column' }} style={{ height: '100%' }} className='pf-v6-u-justify-content-space-between'>
        <FlexItem>
        <span style={{ fontSize: 'var(--pf-t--global--font--size--300)' }}>
            {props.title}
            {props.tooltip && (
              <Tooltip content={props.tooltip}>
                <Icon size="md" className="pf-v6-u-ml-sm">
                  <OutlinedQuestionCircleIcon />
                </Icon>
              </Tooltip>
            )}
          </span>
        </FlexItem>
          
        {link && <FlexItem>{link}</FlexItem>}
          
        <FlexItem>
          <span
            style={{
              fontSize: 'var(--pf-t--global--font--size--800)',
              fontWeight: 'var(--pf-t--global--font--weight--300)',
            }}
          >
            {props.result?.toLocaleString('en-US')}
          </span>
        </FlexItem>
      </Flex>

    </>
  );
};
