# banking-statements

[![PyPI version](https://img.shields.io/pypi/v/banking-statements.svg)](https://pypi.org/project/banking-statements/)
[![Python versions](https://img.shields.io/pypi/pyversions/banking-statements.svg)](https://pypi.org/project/banking-statements/)
[![CI](https://github.com/fifoa-labs/banking-statements/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/fifoa-labs/banking-statements/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/fifoa-labs/banking-statements/branch/main/graph/badge.svg)](https://codecov.io/gh/fifoa-labs/banking-statements)
[![License](https://img.shields.io/pypi/l/banking-statements.svg)](https://github.com/fifoa-labs/banking-statements/blob/main/LICENSE)

Deterministic parsing, normalization, and validation of U.S. banking statements
across institutions, account families, and historical statement formats.

`banking-statements` is a typed Python library for turning supported bank
statements into normalized Python domain objects while preserving the source
evidence needed to understand how each result was produced.

The library is designed around isolated statement processors. Each processor
owns a known statement family and grammar, allowing support for additional
banks and statement revisions to be added without destabilizing processors
already proven against historical statements.

The project emphasizes strict and deterministic behavior. Unsupported statement
formats, ambiguous processor matches, malformed recognized data, unknown
statement behavior, and reconciliation failures during archive validation are
surfaced explicitly rather than silently ignored or guessed around.

Version `0.6.0` expands the package to four supported institutions:

```text
Chase
Wells Fargo
American Express
Discover
```

Implemented processors cover consumer and business deposit accounts, credit
cards, home-equity and business lines of credit, and personal loans. The
processors are developed against private historical statement corpora while
public tests remain fully synthetic and contain no private financial data.

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
banking-statements 0.6.0
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
    credit card
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

American Express
    personal credit card
    business credit card
    business checking
    business line of credit
    personal loan
    observed archive coverage spanning 2013–2026

Discover
    checking
        Cashback Checking
        Cashback Debit
        legacy and current statement layouts
        observed formats spanning 2018–2026

    credit card
        legacy transaction/post-date layouts
        current single-date transaction layouts
        payments and credits
        purchases
        fees
        interest
        observed formats spanning 2019–2025
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

Supported account types currently include:

```text
CHECKING
SAVINGS
CREDIT_CARD
LINE_OF_CREDIT
LOAN
```

The complete private statement archive currently validates:

```text
1963 / 1963 PASS
reconciliation=PASS
difference=0.00
```

That archive total consists of the previously proven Chase and Wells Fargo
corpora plus:

```text
American Express
    692 / 692 PASS

Discover checking
    200 / 200 PASS

Discover credit card
    70 / 70 PASS
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
processors for supported Chase, Wells Fargo, American Express, and Discover
statement families.

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

Stable processor identifiers are intentionally account-family specific.
Examples include:

```text
chase.credit_card.v1
chase.checking.v1
chase.heloc.v1

discover.checking.v1
discover.credit_card.v1
```

Processor identity is part of source evidence and should remain stable for a
supported grammar.

## Chase Credit Card Support

Chase credit-card statements are handled through:

```text
chase.credit_card.v1
```

The processor supports compatible modern, historical, and co-branded Chase
credit-card statement grammars observed in the private development corpus from
2019 through 2026.

The implementation intentionally tolerates only known PDF text-extraction
artifacts demonstrated by real statements. Examples include variants such as
`Opening/Closing Date` versus the extracted form `O\`pening/Closing Date`, and
`New Balance` versus `N\`ew Balance`. Broad fuzzy matching and generic character
de-duplication are intentionally avoided.

Historical statements may expose full account numbers while newer statements
may expose masked numbers. `AccountIdentity` preserves the display value stated
by the source document and separately exposes the last four digits when
available.

Supported activity includes:

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
statements spanning observed formats from 2019 through 2026:

```text
182 / 182 PASS
reconciliation=PASS
difference=0.00
```

The parser supports statement identity, reporting periods, beginning and ending
balances, transaction-detail tables, multi-page activity sections, wrapped
transaction descriptions, deposits, withdrawals, ACH activity, card payments,
transfers, fees, credits, cross-year transaction dates, debit/credit
normalization, and statement reconciliation.

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
allocation detail, funds applied, and funds reversed so statement bookkeeping
is not double-counted.

Finance charges are parsed from the statement's finance-charge calculation
section rather than inferred from the closing summary alone. This matters when
interest accrues and is paid within the same statement cycle, including payoff
cycles where the closing summary may report no remaining interest even though
finance charges accrued during the period.

The processor also supports zero-activity statements and credit-balance
statements where the reported balance is negative.

## Wells Fargo Support

Wells Fargo support covers:

```text
checking
credit card
business checking
business credit card
business line of credit
```

The processors normalize supported consumer and business statements into the
same domain used by every other institution.

Wells Fargo support includes account identity, statement periods, opening and
closing balances, transaction reconstruction, debit/credit normalization,
source evidence, and account-type-aware reconciliation.

The Wells Fargo business line-of-credit processor uses layout-aware PDF evidence
where column position carries transaction direction. This is an intentional
example of the package treating PDF layout as source evidence when flattened
text alone is insufficient to preserve financial meaning.

## American Express Support

American Express support was introduced for `0.5.0` and is included in
`0.6.0`.

Supported account families are:

```text
personal credit card
business credit card
business checking
business line of credit
personal loan
```

The complete American Express private archive currently validates:

```text
692 / 692 PASS
reconciliation=PASS
difference=0.00
```

The archive includes statement evidence spanning 2013 through 2026 and covers
multiple historical layouts and extraction grammars.

American Express credit-card support reconstructs payments, credits, charges,
fees, and interest while preserving source context such as card-ending sections
and supported continuation detail.

Business checking support normalizes deposit-account activity and uses
asset-account reconciliation:

```text
opening balance
+ credits
- debits
= closing balance
```

Business line-of-credit and personal-loan support use debt-account
reconciliation:

```text
opening balance
+ debits
- credits
= closing balance
```

The personal-loan work introduced first-class `LOAN` account support to the
generic domain rather than encoding loan semantics as a special case inside one
processor.

## Discover Checking Support

Discover checking statements are handled through:

```text
discover.checking.v1
```

The processor has been validated against two private account archives totaling
200 monthly statements:

```text
200 / 200 PASS
reconciliation=PASS
difference=0.00
```

Observed statement formats span 2018 through 2026.

The supported archive includes the evolution from:

```text
CASHBACK CHECKING
```

to:

```text
CASHBACK DEBIT
```

and the transition from legacy `DiscoverBank.com` statement branding to current
`Discover.com` branding.

The processor supports:

```text
legacy account-ending identity
current full account-number identity
statement-period parsing
beginning and ending balances
multi-page ACCOUNT ACTIVITY sections
shared activity headers across subsections
Deposits and Credits
Checks
ATM and Debit Card Withdrawals
Electronic Withdrawals
fees and other withdrawals
service charges
zero-activity statements
```

Discover checking activity historically used:

```text
Eff. Date
Bus. Date
```

and later:

```text
Eff. Date
Syst. Date
```

The normalized transaction date uses the statement's posting/system date when
available because that is the date Discover identifies as the date the
transaction is generally processed and posted.

## Discover Credit Card Support

Discover credit-card statements are handled through:

```text
discover.credit_card.v1
```

The private Discover credit-card archive currently validates:

```text
70 / 70 PASS
reconciliation=PASS
difference=0.00
```

Observed formats span 2019 through 2025.

Two major statement grammars are supported.

Legacy statements expose separate transaction and posting dates:

```text
Trans. Date
Post Date
```

Newer statements expose a single transaction-date column.

For legacy statements, the normalized transaction date prefers the reported
posting date. For newer statements, the reported transaction date is resolved
relative to the statement closing date. This intentionally allows statement
activity whose printed transaction date precedes the nominal billing-period
start when the statement itself reports that activity in the current cycle.

Supported economic activity includes:

```text
payments and credits
purchases
fees
interest
```

Fee and interest activity is normalized from the statement's period totals.
This avoids double-counting when the same interest amount is also broken out by
interest category elsewhere in the statement.

The processor also tolerates a proven PDF extraction artifact where text from
an adjacent rewards column can appear after a complete transaction amount.
That adjacent-column text is preserved in raw source evidence but is not
silently appended to the transaction description.

## Statement Balances

Supported statements expose generic balance checkpoints:

```python
StatementBalanceSummary(
    opening_balance=...,
    closing_balance=...,
)
```

These values are parsed as stated by the bank. They are not rewritten to force
reconciliation.

A parser is responsible for understanding the statement grammar. Reconciliation
then independently verifies whether normalized economic activity explains the
reported balance movement.

## Reconciliation

Reconciliation is optional and separate from parsing.

```python
from banking_statements.reconciliation import reconcile_statement

result = reconcile_statement(statement)
```

Reconciliation is account-type aware.

For debt accounts such as credit cards, lines of credit, and loans:

```text
opening balance
+ parsed debits
- parsed credits
= expected closing balance
```

For asset accounts such as checking and savings:

```text
opening balance
+ parsed credits
- parsed debits
= expected closing balance
```

The result includes parsed debit and credit totals, expected closing balance,
difference, and a `reconciled` boolean. A mismatch does not rewrite the parsed
statement.

The private archive smoke tooling is stricter by default and treats a
reconciliation mismatch as a smoke failure so incomplete or misdirected
activity is surfaced during development.

Reconciliation is therefore not a parser shortcut. It is an independent
validation layer used to prove that the extracted financial activity is
economically complete.

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

Normalized transaction amounts use positive magnitudes. Economic direction is
represented separately by `TransactionDirection`.

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

This provenance is important for auditing parser behavior, debugging future
statement revisions, and verifying reconciliation decisions.

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
focused economic normalization
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

Institution-specific extraction behavior belongs in processors. Generic
financial meaning belongs in the domain.

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

Multiple proven historical layouts can remain inside one processor when they
belong to the same statement family and can be distinguished explicitly without
weakening the processor's failure behavior.

## Institution Detection

Institution detection uses explicit marker signatures derived from observed
statement evidence.

A signature should be specific enough to identify the institution without
claiming unrelated documents from the same company.

Institution detection and processor selection are separate steps:

```text
statement text
    ↓
institution signature
    ↓
institution
    ↓
processor registry
    ↓
exact supported account-family processor
```

New signatures should be added because an observed document requires them, not
because a broader marker seems theoretically convenient.

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

Same institution, new account family?
    → add an isolated account-family processor

Same institution and account family, materially different structure?
    → add or explicitly support a proven grammar boundary

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
unexplained reconciliation differences during archive validation
```

Specific failures are preferred over generic parse errors because they make
future statement support easier to develop and audit.

The normal development response to a new archive failure is to inspect the
evidence first, not to make the parser broadly more permissive.

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
adjacent-column bleed
```

When required, processors reconstruct logical rows before attempting to
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
    credit card
    checking
    home-equity line of credit

Wells Fargo
    checking
    credit card
    business checking
    business credit card
    business line of credit

American Express
    personal credit card
    business credit card
    business checking
    business line of credit
    personal loan

Discover
    checking
    credit card
```

A bank, account family, or statement format is listed as supported only after
its processor has been implemented and validated against real statement
evidence.

The complete private development archive currently contains 1963 supported
statements, all of which pass extraction, institution detection, processor
selection, parsing, normalization, and strict reconciliation with zero
difference.

## Private Statement Corpus

Real financial statements used during development are maintained outside the
repository.

The expected local structure is:

```text
private-data/
└── statements/
    ├── chase/
    ├── wellsfargo/
    ├── american-express/
    ├── discover/
    └── ...
```

`private-data/` is excluded from Git.

Real statements, account numbers, transaction histories, names, addresses,
transaction references, balances, and other private financial data must never
be committed to the repository or distributed in package artifacts.

Public tests use generic synthetic statement data.

Synthetic fixtures should preserve only the structural grammar required to
prove parser behavior. They should never copy real names, account numbers,
addresses, merchant references, transaction identifiers, balances, or other
private values from the development archive.

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

Institution processors are validated against private historical statement
archives.

The development workflow is intentionally chronological:

```text
01 PASS
02 PASS
03 PASS
04 FAIL
```

Development stops at the first failure.

That statement is inspected, the failure is classified from actual extracted
evidence, and the smallest correct capability or grammar extension is added.

A generic synthetic regression test is then added before the archive resumes.

Typical usage:

```bash
make smoke-archive \
    folder="private-data/statements/example"
```

Resume from a particular archive position:

```bash
make smoke-archive \
    folder="private-data/statements/example" \
    from=4
```

Limit the run:

```bash
make smoke-archive \
    folder="private-data/statements/example" \
    limit=10
```

Continue after failures when mapping an archive:

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
    private-data/statements/example/statement.pdf \
    --show-transactions
```

Allow reconciliation mismatches for investigation without turning them into
smoke failures:

```bash
uv run python -m scripts.archive_smoke \
    private-data/statements/example \
    --allow-reconciliation-failures
```

Include a traceback while investigating:

```bash
uv run python -m scripts.archive_smoke \
    private-data/statements/example/statement.pdf \
    --show-transactions \
    --allow-reconciliation-failures \
    --traceback
```

The private corpus is a local integration and regression corpus. It is never a
source of public fixture data.

## Development Workflow for New Statement Families

A new account family is developed from evidence rather than from assumptions.

The typical loop is:

```text
1. Run the private archive.
2. Stop at the first failure.
3. Inspect the exact extracted statement text.
4. Compare the failure with existing processor architecture.
5. Implement the narrowest correct grammar or economic rule.
6. Add a generic synthetic regression test.
7. Run formatting, typing, and 100% branch coverage.
8. Re-run the exact failing statement.
9. Resume the archive from that position.
10. Repeat until the complete corpus reconciles exactly.
```

A broader archive scan can be useful for identifying major historical layout
generations, but fixes are still made one proven grammar boundary at a time.

The goal is not merely to make every PDF parse. The goal is to understand why
each supported statement reconciles.

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

A release should also be smoke-validated against the complete supported private
archive before publication.

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
0.6.0
    four-institution statement support

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

    American Express
        personal credit card
        business credit card
        business checking
        business line of credit
        personal loan

    Discover
        checking
        credit card

    account-type-aware reconciliation
    layout-aware PDF evidence
    strict institution detection
    deterministic processor selection
    100% branch coverage
    1963 / 1963 private statements PASS
```

Next evidence-driven institution target:

```text
Capital One
```

Expected later phases:

```text
additional account families for supported institutions
additional institutions
additional historical statement grammars
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
