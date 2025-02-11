import React, { useContext, useState } from 'react';
import { Table, Tbody, Td, Th, ThProps, Thead, Tr } from '@patternfly/react-table';
import { Pagination } from '@patternfly/react-core';
import { CustomInput } from '@app/Components/CustomInput';
import { ParamsContext } from '@app/Store/paramsContext';
import { SortProps, TableResult, columnProps, paginationProps } from '@app/Types';
import { formatCurrency } from '@app/Utils';

export const BaseTable: React.FunctionComponent<{
  pagination: paginationProps;
  data: TableResult[];
  columns: columnProps[];
  sort: SortProps;
  loading: boolean;
  onItemEdit: (value: number, item: TableResult) => void;
}> = (props) => {
  const [activeSortIndex, setActiveSortIndex] = React.useState<number | undefined>(0);
  const [activeSortDirection, setActiveSortDirection] = React.useState<'asc' | 'desc' | undefined>('asc');
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);

  const context = useContext(ParamsContext);
  if (!context) {
    throw new Error('Filters must be used within a ParamsProvider');
  }

  const getSortParams = (columnIndex: number): ThProps['sort'] => ({
    sortBy: {
      index: activeSortIndex,
      direction: activeSortDirection,
    },
    onSort: (_event, index, direction) => {
      setActiveSortIndex(index);
      setActiveSortDirection(direction as 'desc' | 'asc');
      const orderBy = direction === 'asc' ? props.columns[index]['name'] : `-${props.columns[index]['name']}`;
      setPage(1);
      props.sort.onSortChange(orderBy);
    },
    columnIndex,
  });

  const onSetPage = (_event: React.MouseEvent | React.KeyboardEvent | MouseEvent, newPage: number) => {
    setPage(newPage);
    props.pagination.onPageChange(newPage);
  };

  const onPerPageSelect = (_event: React.MouseEvent | React.KeyboardEvent | MouseEvent, newPerPage: number) => {
    setPage(1);
    setPerPage(newPerPage);
    onSetPage(_event, 1);
    props.pagination.onPerPageChange(1, newPerPage);
  };

  const pagination = (
    <Pagination
      titles={{ paginationAriaLabel: 'Table pagination' }}
      itemCount={props.pagination.totalItems}
      perPage={perPage}
      page={page}
      onSetPage={onSetPage}
      onPerPageSelect={onPerPageSelect}
    />
  );

  const handleBlur = (value: number, item: TableResult) => {
    props.onItemEdit(value, item);
  };

  return (
    <>
      <Table aria-label="Sortable table custom toolbar" className="base-table">
        <Thead>
          <Tr>
            {props.columns.map((column, index) => {
              const hasTooltip = column.info && column.info.tooltip;
              return (
                <Th
                  style={{
                    textAlign: column.type === 'number' || column.type === 'currency' ? 'right' : 'left',
                  }}
                  key={column.name}
                  sort={column.isEditable ? undefined : getSortParams(index)}
                  info={hasTooltip ? { tooltip: column.info?.tooltip } : undefined}
                >
                  <span>{column.title}</span>
                </Th>
              );
            })}
          </Tr>
        </Thead>
        <Tbody>
          {props.data.length > 0 ? (
            props.data.map((item, rowNum) => (
              <Tr key={rowNum}>
                {props.columns.map((column) => (
                  <Td
                    key={`${rowNum}-${column.name}`}
                    dataLabel={column['name']}
                    style={{
                      maxWidth: '300px',
                      width: '300px',
                      textAlign: column.type === 'number' || column.type === 'currency' ? 'right' : 'left',
                      paddingRight: column.type === 'number' || column.type === 'currency' ? '32px' : '0',
                    }}
                  >
                    {column.isEditable ? (
                      <div style={{ maxWidth: '250px' }}>
                        <CustomInput
                          type={'number'}
                          id={`${rowNum}-input`}
                          onBlur={(value) => handleBlur(value, item)}
                          value={item[column.name]}
                        />
                      </div>
                    ) : (
                      <div>
                        {column.type === 'currency' ? (
                          <span>{formatCurrency(column.valueKey ? item[column.valueKey] : item[column.name])}</span>
                        ) : (
                          <span>{column.valueKey ? item[column.valueKey] : item[column.name]}</span>
                        )}
                      </div>
                    )}
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
      {props.data.length > 0 && pagination}
    </>
  );
};
