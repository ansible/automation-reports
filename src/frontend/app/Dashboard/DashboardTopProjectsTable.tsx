import React from "react";
import { SimpleTable } from "@app/Components/SimpleTable";
import { useAppSelector } from "@app/hooks";
import { reportProjects } from "@app/Store";
import { Card, CardBody } from "@patternfly/react-core";

export const DashboardTopProjectsTable: React.FunctionComponent = () => {
  const projects = useAppSelector(reportProjects);
  const columns = [
    {
      name: "project_name",
      title: "Project name"
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
        <h2 className="pf-v6-u-font-size-md pf-v6-u-font-weight-bold">Top 5 projects</h2>
        <SimpleTable columns={columns} data={projects}></SimpleTable>
      </CardBody>
    </Card>
    </>
  )
}