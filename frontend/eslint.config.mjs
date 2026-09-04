// Component: Frontend -> Build config -> ESLint
// Belongs to: run via `npm run lint` / the Next.js build's lint step.
// Purpose: standard Next.js recommended lint rules (core-web-vitals + TypeScript),
// with build output directories excluded from linting.

import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
