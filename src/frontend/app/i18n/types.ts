/**
 * TypeScript interfaces for internationalization data structures
 */

export interface LanguageConfig {
  code: string;
  nativeName: string;
  englishName: string;
  direction: 'ltr' | 'rtl';
  isDefault: boolean;
  isTestingOnly?: boolean;
}

export interface I18nPreference {
  language: string;
  isManualSelection: boolean;
  timestamp: number;
}
