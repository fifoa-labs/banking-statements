# banking-statements

[![PyPI version](https://img.shields.io/pypi/v/banking-statements.svg)](https://pypi.org/project/banking-statements/)
[![Python versions](https://img.shields.io/pypi/pyversions/banking-statements.svg)](https://pypi.org/project/banking-statements/)
[![CI](https://github.com/fifoa-labs/banking-statements/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/fifoa-labs/banking-statements/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/fifoa-labs/banking-statements/branch/main/graph/badge.svg)](https://codecov.io/gh/fifoa-labs/banking-statements)
[![License](https://img.shields.io/pypi/l/banking-statements.svg)](https://github.com/fifoa-labs/banking-statements/blob/main/LICENSE)

Deterministic parsing, normalization, and validation of U.S. banking statements
across institutions and statement formats.

`banking-statements` is a typed Python library for turning supported bank
statements into normalized Python domain objects while preserving the source
evidence needed to understand how each result was produced.

The library is designed around isolated statement processors. Each processor
owns a known statement format or revision, allowing support for additional
banks and statement variants to be added without destabilizing processors
already proven against historical statements.

The project emphasizes strict and deterministic behavior. Unsupported statement
formats, ambiguous processor matches, malformed recognized data, and unknown
statement behavior should fail explicitly rather than being silently ignored
or guessed.

Version `0.4.0` expands the package into multi-institution statement support.
Implemented processors now cover Chase credit cards, Chase checking, Chase
home-equity lines of credit, and multiple Wells Fargo consumer and business
statement families. The processors have been developed against private
historical corpora while public tests remain fully synthetic and contain no
private financial data.

The package intentionally focuses on answering:

> What did this bank statement say?

It is not a budgeting application, bank API client, accounting system,
merchant-categorization engine, personal finance manager, tax engine, database
layer, or Beancount-specific importer.

* **PyPI:** https://pypi.org/project/banking-statements/
* **Source:** https://github.com/fifoa-labs/banking-statements
* **License:** MIT

## Current Status

Current release:

```text
banking-statements 0.4.0
```

Supported Python versions:

```text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

Current implemented statement support:

```text
Chase
    credit cards
        modern statement layouts
        historical statement layouts
        co-branded statement layouts
        observed formats spanning 2019–2026

    checking
        Chase Total Checking statements
        multi-page transaction detail
        wrapped transaction descriptions
        observed formats spanning 2019–2026

    home-equity line of credit
        Chase Home Equity Line of Credit statements
        advances and initial funding
        payments and additional-principal payments
        fee assessments and fee payments
        finance-charge accrual
        funds-applied and funds-reversed allocation behavior
        payoff and credit-balance statements
        zero-activity statements
        observed formats spanning 2020–2022

Wells Fargo
    checking
    credit card
    business checking
    business credit card
    business line of credit
```

Current normalized domain includes:

```text
StatementSource
SourceEvidence
StatementPeriod
StatementBalanceSummary
ParsedStatement

AccountType
AccountIdentity

TransactionEvent
TransactionDirection
```

Current Chase credit-card capabilities include account identity, masked and
unmasked account numbers, statement periods, opening and closing balances,
purchases, payments, merchant credits, fees, interest charges, balance
transfers, My Chase Loan activity, promotional adjustments, reversals,
cross-year transaction dates, historical transaction-date references,
foreign-currency continuation preservation, and statement reconciliation.

Current Chase checking capabilities include account identity, statement
periods, beginning and ending balances, signed transaction-table parsing,
multi-page transaction detail, wrapped and continued descriptions, deposits,
withdrawals, ACH activity, card payments, transfers, fees, credits, cross-year
transaction dates, debit/credit normalization, and statement reconciliation.

Current Chase HELOC capabilities include account identity, statement periods,
opening and closing debt balances, advances, initial funding, additional
principal payments, regular payments, fee assessments and fee payments,
finance-charge accrual, funds-applied and funds-reversed allocation behavior,
payoff cycles, negative credit balances, zero-activity cycles, and strict
line-of-credit reconciliation. The private Chase HELOC corpus currently
validates 28 of 28 monthly statements with zero reconciliation difference.

Current Wells Fargo support includes consumer checking and credit-card
statements plus business checking, business credit-card, and business
line-of-credit statement families. The Wells Fargo BusinessLine processor uses
layout-aware PDF evidence where column position carries transaction direction.

The complete private statement archive currently validates:

```text
1001 / 1001 PASS
reconciliation=PASS
difference=0.00
```

Quality gates include Ruff, strict mypy, pytest, 100% branch coverage,
distribution validation, typed-wheel validation, clean-wheel installation,
and full private-archive smoke validation.

## Installation

Install from PyPI:

```bash
pip install banking-statements
```

With `uv`:

```bash
uv add banking-statements
```

Or for development:

```bash
git clone https://github.com/fifoa-labs/banking-statements.git
cd banking-statements
uv sync --dev
```

## Basic Usage

The package exposes generic domain primitives plus implemented statement
processors for supported Chase and Wells Fargo statement families.

```python
from datetime import date
from decimal import Decimal
from pathlib import Path

from banking_statements import (
    StatementPeriod,
    StatementSource,
    TransactionDirection,
    TransactionEvent,
)

source = StatementSource(
    path=Path("statement.pdf"),
    sha256="example-sha256",
)

period = StatementPeriod(
    start=date(2026, 7, 1),
    end=date(2026, 7, 31),
)

transaction = TransactionEvent(
    date=date(2026, 7, 15),
    amount=Decimal("42.17"),
    direction=TransactionDirection.DEBIT,
    description="Sample purchase",
)
```

Chase credit-card statements are handled by the stable processor identifier
`chase.credit_card.v1`.

Chase checking statements are handled by:

```text
chase.checking.v1
```

Chase home-equity line-of-credit statements are handled by:

```text
chase.heloc.v1
```


## Chase Credit Card Support

`0.2.0` includes real Chase credit-card statement support through:

```text
chase.credit_card.v1
```

The processor supports compatible modern, historical, and co-branded Chase
credit-card statement grammars observed in the private development corpus from
2019 through 2026.

The implementation intentionally tolerates only known PDF text-extraction
artifacts demonstrated by real statements. Examples include variants such as `Opening/Closing Date` versus the extracted form
`O\`pening/Closing Date`, and `New Balance` versus `N\`ew Balance`. Broad fuzzy matching and generic character de-duplication are
intentionally avoided.

Historical statements may expose full account numbers while newer statements
may expose masked numbers. `AccountIdentity` preserves the display value stated
by the source document and separately exposes the last four digits when
available.

### Statement balances

Supported statements expose generic balance checkpoints:

```python
StatementBalanceSummary(
    opening_balance=...,
    closing_balance=...,
)
```

These values are parsed as stated by the bank. They are not rewritten to force
reconciliation.

### Supported activity

The Chase credit-card processor currently normalizes activity including:

```text
purchases
payments
merchant credits
fees
interest charges
balance transfers
My Chase Loan activity
promotional adjustments
reversals
```

Normalized amounts are positive magnitudes and `TransactionDirection` carries
the economic direction.


## Chase Checking Support

Chase checking statements are handled through:

```text
chase.checking.v1
```

The processor has been validated against a private chronological corpus of 182
statements spanning observed formats from 2019 through 2026. The complete
private corpus currently passes strict parsing and reconciliation:

```text
182 / 182 PASS
reconciliation=PASS
difference=0.00
```

The parser supports statement identity, reporting periods, beginning and ending
balances, transaction-detail tables, multi-page activity sections, wrapped
transaction descriptions, and normalized checking transactions.

Checking transaction rows are reconstructed from statement text shaped like:

```text
DATE DESCRIPTION AMOUNT BALANCE
```

The signed statement amount is interpreted from the checking account's
perspective:

```text
positive amount
    → CREDIT

negative amount
    → DEBIT
```

Normalized `TransactionEvent.amount` values remain positive magnitudes while
`TransactionDirection` carries the economic direction.

Chase checking statements can include description continuations on later
physical lines. The processor reconstructs those logical rows before economic
normalization rather than silently discarding continuation content.

The running-balance column remains parser evidence from the source statement;
the normalized public transaction model intentionally stays focused on the
transaction date, amount, direction, description, and optional source evidence.


## Chase HELOC Support

Chase home-equity line-of-credit statements are handled through:

```text
chase.heloc.v1
```

The processor has been validated against a private chronological corpus of 28
monthly statements spanning observed formats from 2020 through 2022:

```text
28 / 28 PASS
reconciliation=PASS
difference=0.00
```

The processor normalizes debt-increasing activity such as initial funding,
balance advances, assessed fees, and gross finance charges as debits.
Debt-reducing activity such as additional-principal payments, fee payments, and
funds actually applied to the account is normalized as credits.

Chase HELOC statements expose payment-allocation rows that are not always
independent economic transactions. The processor distinguishes payment
allocation detail, funds applied, and funds reversed so statement bookkeeping is
not double-counted.

Finance charges are parsed from the statement's finance-charge calculation
section rather than inferred from the closing summary alone. This matters when
interest accrues and is paid within the same statement cycle, including payoff
cycles where the closing summary may report no remaining interest even though
finance charges accrued during the period.

The processor also supports zero-activity statements and credit-balance
statements where the reported balance is negative.


## Reconciliation

Reconciliation is optional and separate from parsing.

```python
from banking_statements.reconciliation import reconcile_statement

result = reconcile_statement(statement)
```

Reconciliation is account-type aware.

For debt accounts such as credit cards and lines of credit:

```text
opening balance
+ parsed debits
- parsed credits
= expected closing balance
```

For deposit accounts such as checking and savings:

```text
opening balance
+ parsed credits
- parsed debits
= expected closing balance
```

The result includes the parsed debit and credit totals, expected closing
balance, difference, and a `reconciled` boolean. A mismatch does not modify or
reject the parsed statement.

The private archive smoke tooling is stricter by default and treats a
reconciliation mismatch as a smoke failure so incomplete or misdirected
activity is surfaced during development.

## Financial Values

Financial values use `Decimal`.

```python
from decimal import Decimal

from banking_statements import to_decimal

assert to_decimal("123.45") == Decimal("123.45")
assert to_decimal("$1,234.56") == Decimal("1234.56")
assert to_decimal("(42.17)") == Decimal("-42.17")
```

Floating-point arithmetic is intentionally avoided for normalized financial
values.

## Source Evidence

Normalized statement data should remain traceable to the source statement.

```python
from pathlib import Path

from banking_statements import SourceEvidence, StatementSource

source = StatementSource(
    path=Path("statement.pdf"),
    sha256="example-sha256",
)

evidence = SourceEvidence(
    source=source,
    page=2,
    section="Account Activity",
    raw_text="07/15 SAMPLE PURCHASE 42.17",
    processor="example.monthly",
    sequence=14,
)
```

Evidence can preserve information such as:

```text
source file identity
page
section
raw text
processor
sequence
```

This provenance is important for auditing parser behavior and for future
reconciliation layers.

## Architecture

The implemented processing pipeline is:

```text
PDF
    ↓
PdfStatementTextReader
    ↓
page-aware, layout-aware StatementText
    ↓
institution detection
    ↓
processor selection
    ↓
identity and statement-balance parsing
    ↓
logical transaction rows
    ↓
focused economic parsing
    ↓
ParsedStatement
    ↓
optional reconciliation
```

The architecture separates document mechanics from normalized financial
meaning.

The domain layer should not depend on:

```text
PDF layouts
regular expressions
specific banks
Django
databases
Beancount
application frameworks
```

## Processor Model

Processors represent known statement grammars.

Conceptually:

```python
class StatementProcessor(Protocol):
    @property
    def name(self) -> str: ...

    def match(
        self,
        text: StatementText,
    ) -> ProcessorMatch: ...

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement: ...
```

Processors should be narrow enough that previously proven behavior remains
stable as the package grows.

A materially different statement structure should generally receive a new
processor rather than turning an existing processor into an increasingly broad
universal parser.

## Deterministic Processor Selection

`ProcessorRegistry` requires exactly one compatible processor.

```text
0 matches
    → UnsupportedStatementError

1 match
    → selected

2 or more matches
    → AmbiguousProcessorError
```

There is intentionally no "first matching processor wins" behavior.

Processor registration order must not silently resolve ambiguous statement
formats.

## Development Philosophy

The central maintenance rule is:

> Proven behavior stays stable.

When a future statement fails, the failure should first be classified.

```text
New institution?
    → add institution detection and processor support

Same institution, materially different statement structure?
    → add a new processor

Same processor, new economic capability?
    → add a focused capability module

Same capability, legitimate new grammar?
    → extend only that capability

Unknown or ambiguous input?
    → fail loudly
```

The package should grow as a library of proven document grammars rather than as
one parser that attempts to understand every possible statement.

## Strict Failure Policy

A parser success should mean that the known statement grammar was understood.

The package should not silently discard or guess around:

```text
unknown transaction rows
unknown required sections
ambiguous processor matches
ambiguous amounts
unsupported date grammar
malformed recognized rows
unresolved statement identity
invalid normalized output
```

Specific failures are preferred over generic parse errors because they make
future statement support easier to develop and audit.

## Logical Rows

PDF extraction often does not produce one physical line per financial
transaction.

Real statements may contain:

```text
wrapped descriptions
continuation lines
multi-line ACH details
fragmented columns
inherited dates
page breaks inside tables
```

When required, processors should reconstruct logical rows before attempting to
normalize economic meaning.

```text
physical extracted lines
    ↓
logical statement rows
    ↓
economic normalization
```

This keeps layout reconstruction separate from transaction interpretation.

## Institution Support

Current implemented support:

```text
Chase
    credit cards
    checking
    home-equity line of credit

Wells Fargo
    checking
    credit card
    business checking
    business credit card
    business line of credit
```

Chase credit-card and checking processors have been validated against broad
private historical corpora covering observed statement formats from 2019
through 2026. Chase HELOC support has been validated against 28 monthly
statements covering observed formats from 2020 through 2022.

The complete private development archive currently contains 1001 supported
statements, all of which pass extraction, detection, processor selection,
parsing, normalization, and strict reconciliation with zero difference.

A bank or statement format is listed as supported only after its processor has
been implemented and validated against real statement evidence.

## Private Statement Corpus

Real financial statements used during development are maintained outside the
repository.

The expected local structure is:

```text
private-data/
└── statements/
    ├── institution-a/
    ├── institution-b/
    └── ...
```

`private-data/` is excluded from Git.

Real statements, account numbers, transaction histories, names, addresses, and
other private financial data must never be committed to the repository or
distributed in package artifacts.

Public tests use synthetic statement data.

## Statement Inspection

Development includes tooling for inspecting the exact text extracted from a PDF
statement.

```bash
make inspect-statement \
    file="private-data/statements/example/statement.pdf"
```

Inspect a specific page:

```bash
make inspect-statement \
    file="private-data/statements/example/statement.pdf" \
    page=2
```

Optionally limit displayed text:

```bash
make inspect-statement \
    file="private-data/statements/example/statement.pdf" \
    head=3000
```

Parser behavior should be developed against the text actually returned by the
package's PDF extraction layer rather than assumptions based only on how a PDF
looks visually.

## Archive Smoke Testing

Institution processors will be validated against private historical statement
archives.

The development workflow is intentionally chronological:

```text
01 PASS
02 PASS
03 PASS
04 FAIL
```

Development stops at the first failure.

That statement is inspected, the failure is classified, and the smallest
correct capability is added.

Then the archive is rerun from the beginning.

Typical usage:

```bash
make smoke-archive \
    folder="private-data/statements/example"
```

Limit the run:

```bash
make smoke-archive \
    folder="private-data/statements/example" \
    limit=10
```

Continue after failures when investigating an archive:

```bash
make smoke-archive \
    folder="private-data/statements/example" \
    continue=1
```

A strict smoke PASS means:

```text
document extraction succeeded
institution detection succeeded
processor selection succeeded
statement identity parsed
statement period parsed
opening and closing balances parsed
logical activity reconstructed
transactions normalized
debit/credit direction assigned
statement reconciliation succeeded
```

Run a single statement and print normalized transactions:

```bash
uv run python -m scripts.archive_smoke \
    private-data/statements/chase/credit-card/example.pdf \
    --show-transactions
```

Allow reconciliation mismatches for investigation without turning them into
smoke failures:

```bash
uv run python -m scripts.archive_smoke \
    private-data/statements/chase/credit-card \
    --allow-reconciliation-failures
```

## Development

Install development dependencies:

```bash
uv sync --dev
```

Format:

```bash
make format
```

Check formatting:

```bash
make format-check
```

Lint:

```bash
make lint
```

Type check:

```bash
make typecheck
```

Run tests:

```bash
make test
```

Run tests in parallel:

```bash
make test-fast
```

Run branch coverage:

```bash
make coverage
```

The project maintains:

```text
100% branch coverage
```

## Quality Gates

Run the normal validation suite:

```bash
make check
```

Run the CI-equivalent validation pipeline:

```bash
make ci
```

Before preparing a release:

```bash
make release-check
```

The release check validates:

```text
formatting
linting
mypy
100% branch coverage
distribution build
distribution metadata
typed wheel contents
clean-wheel installation
```

## Build

Build the source distribution and wheel:

```bash
make build
```

Validate distributions:

```bash
make check-dist
```

Inspect wheel contents:

```bash
make wheel-contents
```

Install the built wheel into a clean environment:

```bash
make install-wheel
```

The distributed wheel includes:

```text
banking_statements/py.typed
```

so type information is available to downstream type checkers.

## Dependency Management

The project uses `uv`.

Synchronize the development environment:

```bash
make sync
```

Refresh the lockfile:

```bash
make lock
```

Upgrade dependencies:

```bash
make upgrade
```

`uv.lock` is committed so CI and local release validation can use reproducible
locked environments.

After changing package metadata or dependencies, refresh the lockfile before
committing when required:

```bash
uv lock
```

## Python Support

Supported Python versions:

```text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

CI validates the full supported version matrix.

## Typing

`banking-statements` is a typed package.

The project uses strict mypy checking during development:

```bash
make typecheck
```

The wheel includes the PEP 561 marker:

```text
banking_statements/py.typed
```

## Scope

The package is intentionally narrow.

It aims to provide:

```text
bank statement parsing
statement normalization
source and layout evidence
processor selection
strict statement validation
account-type-aware reconciliation
typed Python domain objects
```

It does not aim to provide:

```text
online banking access
bank API integrations
budgeting
merchant categorization
tax accounting
bookkeeping rules
ledger rendering
Beancount-specific output
Django integration
database models
REST APIs
background jobs
web interfaces
```

Those concerns can consume the normalized statement objects produced by this
package without becoming responsibilities of the statement parser itself.

## Roadmap

Current milestone:

```text
0.4.0
    multi-institution statement support

    Chase
        credit card
        checking
        home-equity line of credit

    Wells Fargo
        checking
        credit card
        business checking
        business credit card
        business line of credit

    account-type-aware reconciliation
    layout-aware PDF evidence
    strict processor selection
    1001 / 1001 private statements PASS
```

Expected next phases:

```text
additional Chase account families when supported by evidence
additional institutions
additional statement grammars
additional reconciliation capabilities when required by statement evidence
```

The roadmap is evidence-driven.

Modules and abstractions should be added because real statement formats require
them, not because they appear theoretically useful.

## Contributing

Contributions are welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes.

The most important contribution rule is:

> New evidence should extend the system at the smallest correct boundary without
> destabilizing previously proven processors.

Never include real private financial statements or personally identifiable
financial information in issues, pull requests, tests, or commits.

## Security

Please report security issues according to [SECURITY.md](SECURITY.md).

Do not disclose private financial information or credentials in public security
reports.

## License

`banking-statements` is released under the MIT License.

See [LICENSE](LICENSE) for details.
