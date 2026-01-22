/**
 * Language Switcher Component
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dropdown,
  DropdownItem,
  DropdownList,
  MenuToggle,
  MenuToggleElement,
} from '@patternfly/react-core';
import { GlobeIcon } from '@patternfly/react-icons';
import { SUPPORTED_LANGUAGES } from './languages';

export const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = React.useState(false);

  const productionLanguages = SUPPORTED_LANGUAGES.filter((lang) => !lang.isTestingOnly);

  const handleLanguageChange = (languageCode: string) => {
    i18n.changeLanguage(languageCode);
    setIsOpen(false);

    const preference = {
      language: languageCode,
      isManualSelection: true,
      timestamp: Date.now(),
    };
    try {
      localStorage.setItem('automation-dashboard-i18n', JSON.stringify(preference));
    } catch (error) {
      console.warn('Could not save language preference to localStorage:', error);
    }
  };

  const onToggle = () => {
    setIsOpen(!isOpen);
  };

  const onSelect = () => {
    setIsOpen(false);
  };

  return (
    <Dropdown
      isOpen={isOpen}
      onSelect={onSelect}
      onOpenChange={(isOpen: boolean) => setIsOpen(isOpen)}
      toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
        <MenuToggle
          ref={toggleRef}
          onClick={onToggle}
          isExpanded={isOpen}
          icon={<GlobeIcon />}
          aria-label="Select Language"
        >
          {productionLanguages.find((lang) => lang.code === i18n.language)?.nativeName || 'Select Language'}
        </MenuToggle>
      )}
    >
      <DropdownList>
        {productionLanguages.map((language) => (
          <DropdownItem
            key={language.code}
            value={language.code}
            onClick={() => handleLanguageChange(language.code)}
            isSelected={i18n.language === language.code}
          >
            {language.nativeName}
          </DropdownItem>
        ))}
      </DropdownList>
    </Dropdown>
  );
};
