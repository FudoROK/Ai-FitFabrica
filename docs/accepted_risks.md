# Accepted Risks

## Next.js Transitive PostCSS Advisory

- Status: accepted moderate risk pending a safe upstream upgrade
- Detected: 2026-06-15
- Advisory: `GHSA-qx2v-qp2m-jg93`
- Production dependency path: `next@16.2.9 -> postcss@8.4.31`
- Safe path already present: `@tailwindcss/postcss@4.2.4 -> postcss@8.5.14`
- Current `npm audit` remediation proposes `npm audit fix --force` and a breaking Next.js downgrade/change.
- Decision: do not run forced remediation. Track a safe Next.js release that updates its bundled PostCSS dependency, then upgrade through normal regression verification.

