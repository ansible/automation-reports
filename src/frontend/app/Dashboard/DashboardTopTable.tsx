import React from 'react';
import { SimpleTable } from '@app/Components';
import { Card, CardBody } from '@patternfly/react-core';
import { DashboardTopTableProps } from '@app/Types';

export const DashboardTopTable: React.FunctionComponent<DashboardTopTableProps> = (props: DashboardTopTableProps) => {
  return (
    <>
      <Card style={{ height: 'inherit' }}>
        <CardBody>
          <h2 className="pf-v6-u-font-size-md pf-v6-u-font-weight-bold" style={{ paddingBottom: '14px' }}>{props.title}</h2>
          <SimpleTable columns={props.columns} data={props?.data ? props.data : []}></SimpleTable>
        </CardBody>
      </Card>
    </>
  );
};
