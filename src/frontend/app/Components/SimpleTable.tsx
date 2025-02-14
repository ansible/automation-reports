import React from 'react';
import { Table, Thead, Tr, Th, Tbody, Td } from '@patternfly/react-table';
import '../styles/table.scss';

interface TableColumn {
  name: string;
  title: string;
}

interface TableProps {
  columns: TableColumn[];
  data: any[];
}

export const SimpleTable: React.FunctionComponent<TableProps> = (props) => {
  return (
    <>
      <Table>
        <Thead>
          <Tr>
            {props.columns.map((column) => (
              <Th key={column.name}>{column.title}</Th>
            ))}
          </Tr>
        </Thead>
        <Tbody>
          {props.data.length > 0 ? (
            props.data.map((item, rowNum) => (
              <Tr key={rowNum}>
                {props.columns.map((column) => (
                  <Td key={item[column.name]} dataLabel={column['title']}>
                    {item[column.name]}
                  </Td>
                ))}
              </Tr>
            ))
          ) : (
            <Tr>
              <Td
                colSpan={props.columns.length}
                style={{ textAlign: 'center' }}
                className="pf-v6-u-font-size-xl pf-v6-u-font-weight-bold pf-v6-u-p-2xl"
              >
                No data available
              </Td>
            </Tr>
          )}
        </Tbody>
      </Table>
    </>
  );
};
