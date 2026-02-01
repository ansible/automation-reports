/**
 * i18next Configuration
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import Backend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';
import { getSupportedLanguageCodes } from './languages';

const params = new URLSearchParams(window.location.search);
const pseudolocalizationEnabled = params.get('pseudolocalization') === 'true';

const pseudolocalizationPostProcessor = {
  type: 'postProcessor' as const,
  name: 'pseudolocalization',
  process: function (value: string): string {
    if (!pseudolocalizationEnabled) return value;
    return `»${value}«`;
  },
};

i18n.use(pseudolocalizationPostProcessor);

// Custom detector to handle JSON object in localStorage
const customLocalStorageDetector = {
  name: 'customLocalStorage',
  lookup(options: any) {
    const key = options.lookupLocalStorage || 'automation-dashboard-i18n';
    const stored = localStorage.getItem(key);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (typeof parsed === 'object' && parsed.language) {
          return parsed.language;
        }
        return parsed;
      } catch {
        return stored;
      }
    }
    return undefined;
  }
};

const languageDetector = new LanguageDetector();
languageDetector.addDetector(customLocalStorageDetector);

// Pre-define event listeners to ensure they catch early events
i18n.on('languageChanged', (lng) => {
  console.log('i18n languageChanged to:', lng);
  document.documentElement.setAttribute('lang', lng);
});

// Validate stored language preference
i18n.on('initialized', () => {
  const storedValue = localStorage.getItem('automation-dashboard-i18n');
  if (storedValue) {
    const supportedCodes = getSupportedLanguageCodes();
    let languageCode: string;

    try {
      const parsed = JSON.parse(storedValue);
      languageCode = typeof parsed === 'object' && parsed.language ? parsed.language : parsed;
    } catch {
      languageCode = storedValue;
    }

    if (!supportedCodes.includes(languageCode)) {
      console.warn(`Stored language "${languageCode}" is no longer supported. Falling back to English.`);
      localStorage.removeItem('automation-dashboard-i18n');
      i18n.changeLanguage('en');
    }
  }
});

i18n
  .use(Backend)
  .use(languageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    supportedLngs: getSupportedLanguageCodes(),
    debug: import.meta.env.DEV,
    defaultNS: 'translation',
    ns: ['translation'],
    interpolation: {
      escapeValue: false,
    },
    detection: {
      // Use customLocalStorage instead of native localStorage to support JSON objects
      order: ['querystring', 'customLocalStorage', 'navigator'],
      lookupQuerystring: 'lang',
      lookupLocalStorage: 'automation-dashboard-i18n',
      caches: ['localStorage'],
      cookieMinutes: 0,
    },
    postProcess: pseudolocalizationEnabled ? ['pseudolocalization'] : [],
    react: {
      useSuspense: true,
    },
    keySeparator: false,
    nsSeparator: false,
  }, (err) => {
    if (err) console.error('i18n init error:', err);
    console.log('i18n initialization callback. Current Language:', i18n.language);
  });

export default i18n;
