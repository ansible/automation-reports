export type paginationProps = {
  onPageChange: (newPage: number) => void
  onPerPageChange: (page: number, newPage: number) => void
  totalItems: number;
}

export type  SortProps = {
  onSortChange: (ordering: string) => void;
}

export type columnProps = {
  name: string;
  title: string;
  type?: 'currency' | 'string' | 'number'
  info?: {
    tooltip?: string;
  };
  isEditable?: boolean;
}
