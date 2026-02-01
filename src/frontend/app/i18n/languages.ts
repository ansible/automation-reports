/**
 * Supported Languages Configuration
 */

import { LanguageConfig } from './types';

export const SUPPORTED_LANGUAGES: LanguageConfig[] = [
  {
    code: 'en',
    nativeName: 'English',
    englishName: 'English',
    direction: 'ltr',
    isDefault: true,
  },
  {
    code: 'es',
    nativeName: 'Español',
    englishName: 'Spanish',
    direction: 'ltr',
    isDefault: false,
  },
  {
    code: 'fr',
    nativeName: 'Français',
    englishName: 'French',
    direction: 'ltr',
    isDefault: false,
  },
  {
    code: 'de',
    nativeName: 'Deutsch',
    englishName: 'German',
    direction: 'ltr',
    isDefault: false,
  },
  {
    code: 'zh',
    nativeName: '中文',
    englishName: 'Chinese',
    direction: 'ltr',
    isDefault: false,
  },
  {
    code: 'ja',
    nativeName: '日本語',
    englishName: 'Japanese',
    direction: 'ltr',
    isDefault: false,
  },
  {
    code: 'zu',
    nativeName: '[PSEUDO]',
    englishName: 'Pseudolocalization',
    direction: 'ltr',
    isDefault: false,
    isTestingOnly: true,
  },
];

export function getLanguageByCode(code: string): LanguageConfig | undefined {
  return SUPPORTED_LANGUAGES.find((lang) => lang.code === code);
}

export function getDefaultLanguage(): LanguageConfig {
  return SUPPORTED_LANGUAGES.find((lang) => lang.isDefault) || SUPPORTED_LANGUAGES[0];
}

export function isLanguageSupported(code: string): boolean {
  return SUPPORTED_LANGUAGES.some((lang) => lang.code === code);
}

export function getSupportedLanguageCodes(): string[] {
  return SUPPORTED_LANGUAGES.map((lang) => lang.code);
}
