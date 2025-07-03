import * as React from 'react';
import { PageHeader } from '@patternfly/react-component-groups';
import { PageHeaderProps } from '@patternfly/react-component-groups/src/PageHeader/PageHeader';
import { Button } from '@patternfly/react-core';

const Header: React.FunctionComponent<PageHeaderProps & { onPdfBtnClick: () => void; pdfBtnText?: string }> = ({
  title,
  subtitle,
  pdfBtnText,
  onPdfBtnClick,
}) => (
  <>
    <style>
      {`
        .page-header {
          position: sticky;
          left: 0;
          .pf-v6-c-page__main-section {
            padding: 0;
            max-width: 80%;
          }
          .btn-pdf {
            width: fit-content;
          }
        }
      `}
    </style>
    <div className={'page-header pf-v6-l-flex pf-m-column-on-md pf-m-row-on-xl pf-m-gap-lg pf-v6-u-p-lg'}>
      <PageHeader title={title} subtitle={subtitle} headingClassname="pf-v6-u-w-75vw"></PageHeader>
      {pdfBtnText && (
        <Button onClick={onPdfBtnClick} className={'btn-pdf pf-v6-u-ml-auto-on-xl pf-v6-u-ml-0'} variant="primary">
          {pdfBtnText}
        </Button>
      )}
    </div>
  </>
);

export { Header };
