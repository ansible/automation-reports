import * as React from 'react';
import { PageHeader } from '@patternfly/react-component-groups';
import { PageHeaderProps } from '@patternfly/react-component-groups/src/PageHeader/PageHeader';
import '../styles/header.scss';
import { Button } from '@patternfly/react-core';

const Header: React.FunctionComponent<PageHeaderProps & { onPdfBtnClick: () => void; pdfBtnText?: string }> = ({
  title,
  subtitle,
  pdfBtnText,
  onPdfBtnClick,
}: {
  title: string;
  subtitle: string;
  pdfBtnText?: string;
  onPdfBtnClick: () => void;
}) => (
  <div className={'page-header'}>
    <PageHeader title={title} subtitle={subtitle}></PageHeader>
    {pdfBtnText && (
      <Button onClick={onPdfBtnClick} className={'btn-pdf'}>
        {pdfBtnText}
      </Button>
    )}
  </div>
);

export { Header };
