import React from 'react';
import { SimpleTable } from '@app/Components';
import { Card, CardBody, Icon, Tooltip } from '@patternfly/react-core';
import { DashboardTopTableProps } from '@app/Types';
import { InfoCircleIcon, OutlinedQuestionCircleIcon } from '@patternfly/react-icons';

export const DashboardTopTable: React.FunctionComponent<DashboardTopTableProps> = (props: DashboardTopTableProps) => {
  return (
    <>
      <Card style={{ height: 'inherit' }}>
        <CardBody>
          <h2 className="pf-v6-u-font-size-md pf-v6-u-font-weight-bold" style={{ paddingBottom: '14px' }}>
            {props.title}
            {props.tooltip && (
              <Tooltip content={props.tooltip}>
                <Icon size="md" className="pf-v6-u-ml-sm">
                  {props.infoIcon && (
                  <InfoCircleIcon/>
                  )}
                  {!props.infoIcon && (
                  <OutlinedQuestionCircleIcon />
                  )}
                </Icon>
              </Tooltip>
            )}
          </h2>
          <SimpleTable columns={props.columns} data={props?.data ? props.data : []}></SimpleTable>
        </CardBody>
      </Card>
    </>
  );
};
