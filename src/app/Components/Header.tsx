import * as React from 'react';
import { PageHeader } from '@patternfly/react-component-groups';
import { PageHeaderProps } from '@patternfly/react-component-groups/src/PageHeader/PageHeader';
import '../styles/header.scss';

const Header: React.FunctionComponent<PageHeaderProps> = ({ title, subtitle }: { title: string; subtitle: string }) => (
  <div className={'page-header'}>
    <PageHeader title={title} subtitle={subtitle}></PageHeader>
  </div>
);

export { Header };
