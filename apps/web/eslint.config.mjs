import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import prettier from "eslint-config-prettier";

const config = [
  ...nextVitals,
  ...nextTs,
  // Formatting is Prettier's job (`npm run format`); this switches off the style rules that would disagree.
  prettier,
  {
    ignores: [".next/**", "node_modules/**", "playwright-report/**", "test-results/**", "next-env.d.ts"],
  },
];

export default config;
