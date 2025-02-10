import React from "react";
import { SimpleTable } from "@app/Components/SimpleTable";
import { useAppSelector } from "@app/hooks";
import { reportUsers } from "@app/Store";
import { Card, CardBody } from "@patternfly/react-core";

export const DashboardTopUsersTable: React.FunctionComponent = () => {
  const users = useAppSelector(reportUsers);
  const columns = [
    {
      name: "user_name",
      title: "User name"
    }, 
    {
      name: "count",
      title: "Total time of running jobs"
    }
  ];
  return (
    <>
      <Card className="simple-table-card">
        <CardBody>
          <h2 className="pf-v6-u-font-size-md pf-v6-u-font-weight-bold">Top 5 users</h2>
          <SimpleTable columns={columns} data={users}></SimpleTable>
        </CardBody>
      </Card>
    </>
  )
}