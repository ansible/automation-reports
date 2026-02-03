module.exports = {
  contextSeparator: '_',
  keySeparator: false,
  namespaceSeparator: false,
  createOldCatalogs: true,
  defaultNamespace: 'translation',

  defaultValue: (locale, namespace, key) => {
    if (locale === 'zu') {
      return key
        .toUpperCase()
        .split('')
        .join('_')
        .split('_ _')
        .join(' ')
        .replace(/{_{_C_O_U_N_T_}_}/g, '{{count}}')
        .replace(/{_{_([A-Z_]+)_}_}/g, '{{$1}}');
    }
    return key;
  },

  indentation: 2,
  keepRemoved: false,
  locales: ['en', 'es', 'fr', 'de', 'zh', 'ja', 'zu'],
  output: 'src/frontend/locales/$LOCALE/$NAMESPACE.json',
  pluralSeparator: '_',
  input: ['src/frontend/**/*.tsx', 'src/frontend/**/*.ts'],
  sort: true,
  lineEnding: 'auto',
  skipDefaultValues: false,
  useKeysAsDefaultValue: false,
  verbose: false,
  failOnWarnings: false,
  failOnUpdate: false,
  customValueTemplate: null,
  resetDefaultValueLocale: 'en',
  i18nextOptions: null,

  lexers: {
    hbs: ['HandlebarsLexer'],
    handlebars: ['HandlebarsLexer'],
    htm: ['HTMLLexer'],
    html: ['HTMLLexer'],
    mjs: ['JavascriptLexer'],
    js: ['JavascriptLexer'],
    ts: ['JavascriptLexer'],
    jsx: ['JsxLexer'],
    tsx: ['JsxLexer'],
    default: ['JavascriptLexer']
  }
};
