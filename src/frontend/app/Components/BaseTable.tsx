import React from 'react';
import { Table, Tbody, Td, Th, ThProps, Thead, Tr } from '@patternfly/react-table';
import { Pagination } from '@patternfly/react-core';
import { CustomInput } from '@app/Components';
import { ColumnProps, PaginationProps, SortProps, TableResult } from '@app/Types';
import { deepClone, formatCurrency, formatNumber } from '@app/Utils';
import { useAppSelector } from '@app/hooks';
import { currencySign } from '@app/Store';

export type ColumnError = {
  rowNum: number;
  columnName: string;
  message: string | null;
};

export const BaseTable: React.FunctionComponent<{
  pagination: PaginationProps;
  data: TableResult[];
  columns: ColumnProps[];
  sort: SortProps;
  loading: boolean;
  onItemEdit: (newValue: TableResult, oldValue: TableResult) => void;
  onItemFocus?: (event?: never) => void;
  onItemBlur?: (event?: never) => void;
}> = (props) => {
  const [activeSortIndex, setActiveSortIndex] = React.useState<number | undefined>(0);
  const [activeSortDirection, setActiveSortDirection] = React.useState<'asc' | 'desc' | undefined>('asc');
  const [page, setPage] = React.useState(1);
  const [perPage, setPerPage] = React.useState(10);
  const [editingError, setEditingError] = React.useState<ColumnError | undefined>(undefined);
  const selectedCurrencySign = useAppSelector(currencySign);

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
    setPerPage(newPerPage);
    setPage(1);
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

  const handleBlur = (value: number, item: TableResult, rowNum: number, columnName: string) => {
    if (value < 1) {
      setEditingError({
        rowNum: rowNum,
        columnName: columnName,
        message: 'Value must be greater then 0!',
      });
      return;
    }
    setEditingError(undefined);
    const editedItem = deepClone(item) as TableResult;
    editedItem[columnName] = value;
    props.onItemEdit(editedItem, item);
  };

  const handleFocus = (event?: never) => {
    if (props.onItemFocus) {
      props.onItemFocus(event);
    }
  };

  return (
    <>
      <div style={{ overflowX: 'auto' }}>
        <Table aria-label="Sortable table custom toolbar" className="base-table">
          <Thead>
            <Tr>
              {props.columns.map((column, index) => {
                const hasTooltip = column.info && column.info.tooltip;
                return (
                  <Th
                    className={column.type === 'number' || column.type === 'currency' ? 'numerical' : ''}
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
                      dataLabel={column['title']}
                      className={column.type === 'number' || column.type === 'currency' ? 'numerical' : ''}
                    >
                      {column.isEditable ? (
                        <div
                          style={{ maxWidth: '150px' }}
                          className={
                            editingError?.message &&
                            editingError?.message?.length > 0 &&
                            editingError?.rowNum === rowNum &&
                            editingError?.columnName !== column.name
                              ? 'has-error'
                              : ''
                          }
                        >
                          <CustomInput
                            type={'number'}
                            id={`${rowNum}-${column.name}`}
                            onBlur={(value) => handleBlur(value, item, rowNum, column.name)}
                            value={item[column.name]}
                            errorMessage={
                              editingError &&
                              editingError?.rowNum === rowNum &&
                              editingError.columnName === column.name &&
                              editingError?.message &&
                              editingError?.message?.length > 0
                                ? editingError.message
                                : ''
                            }
                            isDisabled={
                              (editingError &&
                                editingError?.message &&
                                editingError?.message?.length > 0 &&
                                (editingError?.rowNum !== rowNum ||
                                  (editingError?.rowNum === rowNum &&
                                    editingError?.columnName !== column.name))) as boolean
                            }
                            onFocus={handleFocus}
                          />
                        </div>
                      ) : (
                        <div
                          className={
                            editingError &&
                            editingError?.message &&
                            editingError?.message?.length > 0 &&
                            editingError?.rowNum === rowNum
                              ? 'has-error'
                              : ''
                          }
                        >
                          {column.type === 'currency' ? (
                            <span>
                              {formatCurrency(
                                column.valueKey ? item[column.valueKey] : item[column.name],
                                selectedCurrencySign,
                              )}
                            </span>
                          ) : column.type === 'number' ? (
                            <span>{formatNumber(item[column.name])}</span>
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
      </div>
      {props?.data?.length && props?.pagination?.totalItems && props.pagination.totalItems > 10 && pagination}
    </>
  );
};
