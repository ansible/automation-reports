import * as React from 'react';
import { ExclamationTriangleIcon } from '@patternfly/react-icons';
import { Button, EmptyState, EmptyStateBody, EmptyStateFooter, PageSection } from '@patternfly/react-core';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const NotFound: React.FunctionComponent = () => {
  const { t } = useTranslation();

  function GoHomeBtn() {
    const navigate = useNavigate();
    function handleClick() {
      navigate('/');
    }
    return <Button onClick={handleClick}>{t('Take me home')}</Button>;
  }

  return (
    <PageSection hasBodyWrapper={true}>
      <EmptyState titleText={t('404 Page not found')} variant="full" icon={ExclamationTriangleIcon}>
        <EmptyStateBody>{t("We didn't find a page that matches the address you navigated to.")}</EmptyStateBody>
        <EmptyStateFooter>
          <GoHomeBtn />
        </EmptyStateFooter>
      </EmptyState>
    </PageSection>
  );
};

export { NotFound };

