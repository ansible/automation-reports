import { defineConfig } from "eslint/config";
import js from "@eslint/js";
import typescriptEslint from "@typescript-eslint/eslint-plugin";
import typescriptParser from "@typescript-eslint/parser";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";

export default defineConfig([
  {
    ignores: ["**/coverage", "**/dist"],
  },
  {
    files: ["**/*.{js,mjs,cjs,ts,tsx}"],
    languageOptions: {
      parser: typescriptParser,
      parserOptions: {
        project: "./tsconfig.json",
        tsconfigRootDir: ".",
        ecmaVersion: 2021,
        sourceType: "module",
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        window: "readonly",
        describe: "readonly",
        test: "readonly",
        expect: "readonly",
        it: "readonly",
        process: "readonly",
        document: "readonly",
        insights: "readonly",
        shallow: "readonly",
        render: "readonly",
        mount: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": typescriptEslint,
      react,
      "react-hooks": reactHooks,
    },
    settings: {
      react: {
        version: "detect",
      },
    },
    rules: {
      ...js.configs.recommended.rules,
      ...react.configs.recommended.rules,
      ...typescriptEslint.configs["recommended"].rules,
      "sort-imports": ["error", { ignoreDeclarationSort: true }],
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/interface-name-prefix": "off",
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": 0,
      "prettier/prettier": "off",
      "import/no-unresolved": "off",
      "import/extensions": "off",
      "react/prop-types": "off",
    },
  },
  {
    files: ["src/frontend/**/*.ts", "src/frontend/**/*.tsx"],
    languageOptions: {
      parser: typescriptParser,
    },
    plugins: {
      "@typescript-eslint": typescriptEslint,
    },
    rules: {
      ...typescriptEslint.configs["recommended"].rules,
      "react/prop-types": "off",
      "@typescript-eslint/no-unused-vars": "error",
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-empty-object-type": [
        "error",
        { allowObjectTypes: "always" }
      ]
    },
  },
]);