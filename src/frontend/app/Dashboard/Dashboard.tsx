import * as React from 'react';
import { Filters, Header } from '@app/Components';

const Dashboard: React.FunctionComponent = () => (
  <div>
    <Header title={'Automation Savings Service'} subtitle={'Page description'}></Header>
    <div className={'main-layout'}>
      <Filters></Filters>
    </div>
  </div>
);

export { Dashboard };
