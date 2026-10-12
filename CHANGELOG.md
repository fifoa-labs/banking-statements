# Changelog

## 1.0.0

- Establish the stable `parse_statement()` and `parse_statements()` public API.
- Preserve all account results from combined documents; consumers must iterate
  `result.accounts` or use the flattened `parse_statements()` results.
- Accept both Spark Cash business-card header generations.
- Parse AMEX checking minus-sign debits and continued transaction pages.
- Handle Chase checking period and transaction-marker extraction spacing.
- Add development-only archive pruning with a preview manifest, pinned files,
  stale-plan checks, retained coverage verification, and reversible moves.
- Pruning preserves observed branches and tracked features; it does not prove
  semantic equivalence or complete input-grammar coverage.

Validation: 892 tests, 100% package statement and branch coverage, 2,436 local
PDFs validated with zero failures, and the retained 211-PDF corpus smoke-tested.

## 0.12.0

- Add Chime checking, Credit Builder, secured-account, and multi-account support.
- Recover Wells Fargo Way2Save savings from combined checking/savings documents.
