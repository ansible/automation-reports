import React from 'react';
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table';
import '../styles/table.scss';
import { ColumnProps } from '@app/Types';
import { formatNumber } from '@app/Utils';
import { useTranslation } from 'react-i18next';

interface TableProps {
  columns: ColumnProps[];
  data: any[];
}

export const SimpleTable: React.FunctionComponent<TableProps> = (props) => {
  const { t } = useTranslation();

  return (
    <>
      <Table className={'top-table'}>
        <Thead>
          <Tr>
            {props.columns.map((column) => (
              <Th
                className={column.type === 'number' || column.type === 'currency' ? 'numerical' : ''}
                key={column.title}
              >
                {column.title}
              </Th>
            ))}
          </Tr>
        </Thead>
        <Tbody>
          {props.data.length > 0 ? (
            props.data.map((item, rowNum) => (
              <Tr key={rowNum}>
                {props.columns.map((column) => (
                  <Td
                    key={item[column.name]}
                    dataLabel={column['title']}
                    className={column.type === 'number' || column.type === 'currency' ? 'numerical' : ''}
                  >
                    {column.type === 'number' ? formatNumber(item[column.name]) : item[column.name]}
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
                {t('No data available')}
              </Td>
            </Tr>
          )}
        </Tbody>
      </Table>
    </>
  );
};
