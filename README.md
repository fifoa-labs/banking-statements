# banking-statements

[![PyPI
version](https://img.shields.io/pypi/v/banking-statements.svg)](https://pypi.org/project/banking-statements/)
[![Python
versions](https://img.shields.io/pypi/pyversions/banking-statements.svg)](https://pypi.org/project/banking-statements/)
[![CI](https://github.com/fifoa-labs/banking-statements/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/fifoa-labs/banking-statements/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/fifoa-labs/banking-statements/branch/main/graph/badge.svg)](https://codecov.io/gh/fifoa-labs/banking-statements)
[![License](https://img.shields.io/pypi/l/banking-statements.svg)](https://github.com/fifoa-labs/banking-statements/blob/main/LICENSE)

Deterministic parsing, normalization, and validation of U.S. banking
statements across institutions, account families, and historical
statement formats.

`banking-statements` is a typed Python library for turning supported
bank statements into normalized Python domain objects while preserving
the source evidence needed to understand how each result was produced.

The library is designed around isolated statement processors. Each
processor owns a known statement family and grammar, allowing support
for additional banks and statement revisions to be added without
destabilizing processors already proven against historical statements.

The project emphasizes strict and deterministic behavior. Unsupported
statement formats, ambiguous processor matches, malformed recognized
data, unknown statement behavior, and reconciliation failures during
archive validation are surfaced explicitly rather than silently ignored
or guessed around.

Version `0.10.0` adds U.S. Bank support, expanding the package to seven
supported institutions:

``` text
Chase
Wells Fargo
American Express
Discover
Capital One
PenFed
U.S. Bank
```

Implemented processors cover consumer and business deposit accounts,
credit cards, home-equity and business lines of credit, and personal
loans. The processors are developed against private historical statement
corpora while public tests remain fully synthetic and contain no private
financial data.

The package intentionally focuses on answering:

> What did this bank statement say?

It is not a budgeting application, bank API client, accounting system,
merchant-categorization engine, personal finance manager, tax engine,
database layer, or Beancount-specific importer.

-   **PyPI:** https://pypi.org/project/banking-statements/
-   **Source:** https://github.com/fifoa-labs/banking-statements
-   **License:** MIT

## Current Status

Current release:

``` text
banking-statements 0.10.0
```

Supported Python versions:

``` text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

Current implemented statement support:

``` text
Chase
    credit card
        modern statement layouts
        historical statement layouts
        co-branded statement layouts
        observed formats spanning 2019–2026

    business credit card
        Ink Business Cash statements
        Ink Business Unlimited statements
        signed ACCOUNT ACTIVITY transaction tables
        historical multi-cardholder activity
        multi-page ACCOUNT ACTIVITY continuation pages
        payments, refunds, purchases, fees, and interest
        foreign-currency continuation detail
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

Capital One
    credit card
        Venture X consumer credit-card statements
        transaction and posting-date activity
        payments and credits
        purchases
        fees
        interest
        foreign-currency detail preservation
        observed formats spanning 2023–2026

    business credit card
        Spark business credit-card statements
        Venture X Business statements
        legacy flattened two-column transaction layouts
        current transaction/post-date layouts
        payments and credits
        purchases
        fees
        interest where reported
        observed formats spanning 2019–2026

    checking
        360 Checking statements
        monthly and quarterly statement periods
        running-balance transaction validation
        wrapped transfer descriptions and reference lines
        zero-activity statements
        observed formats spanning 2022–2026

PenFed
    home-equity line of credit
        monthly HELOC statements
        principal curtailment payments
        payment receipt and allocation behavior
        returned-payment and NSF reversals
        returned-check fee assessment and reversal
        finance-charge parsing and validation
        legacy single-date activity tables
        current process/effective-date activity tables
        observed formats spanning 2024–2026

U.S. Bank
    business checking
        Silver Business Checking statements
        deposits and withdrawals
        analysis service charges
        wrapped transaction and reference detail
        zero-activity statements
        observed formats spanning 2023–2026

    credit card
        Radisson Rewards Visa statements
        Altitude Go Visa Signature statements
        Platinum Visa statements
        payments and other credits
        purchases and other debits
        fees and fee reversals
        interest charges
        other debits
        multi-page transaction sections
        zero-dollar fee rows
        observed formats spanning 2019–2026
```

Current normalized domain includes:

``` text
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

``` text
CHECKING
SAVINGS
CREDIT_CARD
LINE_OF_CREDIT
LOAN
```

The complete private statement archive currently validates:

``` text
2381 / 2381 PASS
reconciliation=PASS
difference=0.00
```

That archive total consists of the previously proven Chase and Wells
Fargo corpora plus:

``` text
Chase business credit card
    89 / 89 PASS

    Ink Business Cash
        73 / 73 PASS

    Ink Business Unlimited
        16 / 16 PASS

American Express
    692 / 692 PASS

Discover checking
    200 / 200 PASS

Discover credit card
    70 / 70 PASS

Capital One
    199 / 199 PASS

    consumer credit card
        38 / 38 PASS

    business credit card
        86 / 86 PASS

    checking
        75 / 75 PASS

PenFed HELOC
    25 / 25 PASS

U.S. Bank
    105 / 105 PASS

    business checking
        35 / 35 PASS

    credit card
        70 / 70 PASS
```

Quality gates include Ruff, strict mypy, pytest, 100% branch coverage,
distribution validation, typed-wheel validation, clean-wheel
installation, and full private-archive smoke validation.

## Installation

Install from PyPI:

``` bash
pip install banking-statements
```

With `uv`:

``` bash
uv add banking-statements
```

Or for development:

``` bash
git clone https://github.com/fifoa-labs/banking-statements.git
cd banking-statements
uv sync --dev
```

## Using the Package from Another Project

Application code should be institution-independent.

A consuming project should not need to know whether a PDF came from
Chase, Wells Fargo, American Express, Discover, Capital One, PenFed, or
U.S. Bank. Institution names, account-family names, processor
identifiers, folder names, and filename conventions are parser concerns
owned by `banking-statements`.

The intended application boundary is:

``` text
PDF file
    ↓
banking-statements
    ↓
institution detection
    ↓
deterministic processor selection
    ↓
statement parsing
    ↓
ParsedStatement
```

The caller supplies statement PDFs. The package determines whether each
statement belongs to a supported institution and which supported
account-family processor owns its grammar.

This means application code should not contain routing such as:

``` text
if filename contains "chase":
    use Chase parser

if folder == "usbank":
    use U.S. Bank parser

if account ending == "1234":
    use credit-card parser
```

Those rules would duplicate knowledge that belongs inside this package.

### Parse one PDF

The current public building blocks can be composed into a small
institution-independent application function:

``` python
from hashlib import sha256
from pathlib import Path

from banking_statements.domain import ParsedStatement, StatementSource
from banking_statements.processors.defaults import (
    build_default_institution_detector,
    build_default_processor_registry,
)
from banking_statements.text import PdfStatementTextReader


def file_sha256(path: Path) -> str:
    digest = sha256()

    with path.open("rb") as source_file:
        while chunk := source_file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def parse_statement(path: Path) -> ParsedStatement:
    source = StatementSource(
        path=path,
        sha256=file_sha256(path),
    )

    text = PdfStatementTextReader().read(source)

    detector = build_default_institution_detector()
    detector.detect(text)

    registry = build_default_processor_registry()
    processor = registry.select(text)

    return processor.parse(source, text)
```

Usage:

``` python
from pathlib import Path

statement = parse_statement(Path("statement.pdf"))

print(statement.account)
print(statement.period)
print(statement.balances)

for transaction in statement.transactions:
    print(
        transaction.date,
        transaction.direction,
        transaction.amount,
        transaction.description,
    )
```

The calling project does not select an institution or processor.
Detection and processor ownership are resolved from statement evidence.

### Parse a folder of mixed statements

A folder may contain statements from different supported institutions
and account families.

The directory hierarchy is not parser input. Filenames are not parser
input. They are useful for human organization only.

For example, all of these are valid application inputs:

``` text
statements/
├── chase/
│   └── checking/
│       └── 2026-07.pdf
├── usbank/
│   └── credit-card/
│       └── 2026-07.pdf
└── capitalone/
    └── checking/
        └── 2026-07.pdf
```

or the same PDFs flattened and renamed:

``` text
statements/
├── 000001.pdf
├── banana.pdf
├── document-final.pdf
├── random-name-42.pdf
└── x.pdf
```

For supported statement grammars, parsing should produce the same
normalized result in either layout because routing is based on PDF
evidence rather than path conventions.

A consuming project can recursively process a mixed folder:

``` python
from pathlib import Path

folder = Path("statements")

for path in sorted(folder.rglob("*.pdf")):
    statement = parse_statement(path)

    print(
        path,
        statement.account.account_type,
        statement.account.last_four,
        statement.period.start,
        statement.period.end,
        len(statement.transactions),
    )
```

The same loop can process one institution, seven institutions, or any
future institution added to the package without adding
institution-specific routing to the consuming application.

### Reconcile parsed statements

Parsing and reconciliation remain separate operations:

``` python
from banking_statements.reconciliation import reconcile_statement

statement = parse_statement(Path("statement.pdf"))
reconciliation = reconcile_statement(statement)

if not reconciliation.reconciled:
    raise ValueError(
        f"statement did not reconcile: {reconciliation.difference}"
    )
```

Applications can choose their own reconciliation policy. The private
archive smoke tooling treats reconciliation mismatches as failures
because it is a strict development-validation environment.

### Mixed-folder behavior

For each PDF, the package follows the same deterministic sequence:

``` text
read PDF
    ↓
detect exactly one supported institution
    ↓
select exactly one compatible processor
    ↓
parse identity, period, balances, and activity
    ↓
return ParsedStatement
```

If the PDF belongs to an unsupported institution or unsupported
statement grammar, parsing fails explicitly.

If institution evidence is ambiguous, detection fails explicitly.

If zero processors match the recognized statement, processor selection
fails explicitly.

If multiple processors match, processor selection fails explicitly
rather than using registration order, a filename, or a directory name to
guess.

This is intentional. A successful parse should mean that the package
recognized and understood a proven statement grammar.

### Independence from institutions

`banking-statements` is institution-aware internally and
institution-independent at the application boundary.

Internally, the package must understand institution-specific evidence
because real banks publish different statement grammars:

``` text
application
    │
    │ generic PDF input
    ▼
banking-statements
    ├── institution detection
    ├── Chase processors
    ├── Wells Fargo processors
    ├── American Express processors
    ├── Discover processors
    ├── Capital One processors
    ├── PenFed processors
    └── U.S. Bank processors
    │
    │ normalized domain output
    ▼
application
```

The consuming application should normally care about normalized concepts
such as:

``` text
AccountType
AccountIdentity
StatementPeriod
StatementBalanceSummary
TransactionEvent
TransactionDirection
ParsedStatement
```

It should not need to know which institution-specific parser produced
them unless that provenance is useful for auditing or diagnostics.

This separation is a core design goal: adding a new supported
institution or account family should expand what the same application
integration can parse without requiring the application to add a new
institution-specific branch.

### Folder organization is optional

The private development corpus is organized by institution and account
family because that structure is useful for maintenance, historical
investigation, targeted smoke runs, and human navigation.

It is not required for runtime identification.

Conceptually, these two corpora are equivalent parser inputs:

``` text
organized/
├── chase/
├── wellsfargo/
├── american-express/
├── discover/
├── capitalone/
├── penfed/
└── usbank/
```

and:

``` text
flat/
├── 000001.pdf
├── 000002.pdf
├── 000003.pdf
└── ...
```

provided the files themselves are unchanged and each statement grammar
is supported.

The PDF is the source of truth.

## Basic Usage

The package exposes generic domain primitives plus implemented statement
processors for supported Chase, Wells Fargo, American Express, Discover,
Capital One, PenFed, and U.S. Bank statement families.

``` python
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

``` text
chase.credit_card.v1
chase.business_credit_card.v1
chase.checking.v1
chase.heloc.v1

discover.checking.v1
discover.credit_card.v1

capital_one.credit_card.v1
capital_one.business_credit_card.v1
capital_one.checking.v1

penfed.heloc.v1

us_bank.business_checking.v1
us_bank.credit_card.v1
```

Processor identity is part of source evidence and should remain stable
for a supported grammar.

## Chase Credit Card Support

Chase credit-card statements are handled through:

``` text
chase.credit_card.v1
```

The processor supports compatible modern, historical, and co-branded
Chase credit-card statement grammars observed in the private development
corpus from 2019 through 2026.

The implementation intentionally tolerates only known PDF
text-extraction artifacts demonstrated by real statements. Examples
include variants such as `Opening/Closing Date` versus the extracted
form `O\`pening/Closing Date`, and`New Balance`versus`N\`ew Balance\`.
Broad fuzzy matching and generic character de-duplication are
intentionally avoided.

Historical statements may expose full account numbers while newer
statements may expose masked numbers. `AccountIdentity` preserves the
display value stated by the source document and separately exposes the
last four digits when available.

Supported activity includes:

``` text
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

Normalized amounts are positive magnitudes and `TransactionDirection`
carries the economic direction.

## Chase Business Credit Card Support

Chase business credit-card statements are handled through:

``` text
chase.business_credit_card.v1
```

The private Chase business credit-card archive currently validates:

``` text
89 / 89 PASS
reconciliation=PASS
difference=0.00
```

That corpus consists of four account archives:

``` text
Ink Business Cash
    73 / 73 PASS

Ink Business Unlimited
    16 / 16 PASS
```

Observed statement formats span 2019 through 2026.

Chase business credit-card statements use a different activity grammar
from the consumer Chase credit-card processor. Rather than relying on
category sections such as `PURCHASE` or `PAYMENTS AND OTHER CREDITS`,
the supported business-card family exposes signed economic rows inside
`ACCOUNT ACTIVITY`.

The statement amount carries direction:

``` text
positive amount
    → DEBIT

negative amount
    → CREDIT
```

Normalized `TransactionEvent.amount` values remain positive magnitudes
while `TransactionDirection` carries the economic direction.

The processor supports:

``` text
purchases
payments
merchant refunds and credits
fees
interest
credit-balance refunds
foreign-currency continuation detail
historical multi-cardholder activity
multi-page ACCOUNT ACTIVITY continuation pages
zero-activity statements
cross-year transaction dates
```

Historical business statements can contain multiple cardholder
subsections in one account-activity table. Each cardholder subtotal is
statement bookkeeping, not an independent transaction. The processor
reconstructs the dated economic rows across those subsections without
treating cardholder labels or `TRANSACTIONS THIS CYCLE` totals as
activity.

Modern high-volume statements can continue activity onto later physical
pages under `ACCOUNT ACTIVITY (CONTINUED)`. The parser preserves
transaction order across those page boundaries and keeps supported
continuation detail attached to the correct transaction.

Foreign-currency purchases can expose the original currency and
exchange-rate detail on following lines. That detail is preserved as
source evidence without being silently converted into a second economic
transaction.

This account family has its own processor rather than broadening
`chase.credit_card.v1`. Consumer and business Chase credit-card matching
are kept mutually exclusive so the processor registry retains
deterministic, single-processor selection.

## Chase Checking Support

Chase checking statements are handled through:

``` text
chase.checking.v1
```

The processor has been validated against a private chronological corpus
of 182 statements spanning observed formats from 2019 through 2026:

``` text
182 / 182 PASS
reconciliation=PASS
difference=0.00
```

The parser supports statement identity, reporting periods, beginning and
ending balances, transaction-detail tables, multi-page activity
sections, wrapped transaction descriptions, deposits, withdrawals, ACH
activity, card payments, transfers, fees, credits, cross-year
transaction dates, debit/credit normalization, and statement
reconciliation.

Checking transaction rows are reconstructed from statement text shaped
like:

``` text
DATE DESCRIPTION AMOUNT BALANCE
```

The signed statement amount is interpreted from the checking account's
perspective:

``` text
positive amount
    → CREDIT

negative amount
    → DEBIT
```

Normalized `TransactionEvent.amount` values remain positive magnitudes
while `TransactionDirection` carries the economic direction.

Chase checking statements can include description continuations on later
physical lines. The processor reconstructs those logical rows before
economic normalization rather than silently discarding continuation
content.

The running-balance column remains parser evidence from the source
statement; the normalized public transaction model intentionally stays
focused on the transaction date, amount, direction, description, and
optional source evidence.

## Chase HELOC Support

Chase home-equity line-of-credit statements are handled through:

``` text
chase.heloc.v1
```

The processor has been validated against a private chronological corpus
of 28 monthly statements spanning observed formats from 2020 through
2022:

``` text
28 / 28 PASS
reconciliation=PASS
difference=0.00
```

The processor normalizes debt-increasing activity such as initial
funding, balance advances, assessed fees, and gross finance charges as
debits. Debt-reducing activity such as additional-principal payments,
fee payments, and funds actually applied to the account is normalized as
credits.

Chase HELOC statements expose payment-allocation rows that are not
always independent economic transactions. The processor distinguishes
payment allocation detail, funds applied, and funds reversed so
statement bookkeeping is not double-counted.

Finance charges are parsed from the statement's finance-charge
calculation section rather than inferred from the closing summary alone.
This matters when interest accrues and is paid within the same statement
cycle, including payoff cycles where the closing summary may report no
remaining interest even though finance charges accrued during the
period.

The processor also supports zero-activity statements and credit-balance
statements where the reported balance is negative.

## Wells Fargo Support

Wells Fargo support covers:

``` text
checking
credit card
business checking
business credit card
business line of credit
```

The processors normalize supported consumer and business statements into
the same domain used by every other institution.

Wells Fargo support includes account identity, statement periods,
opening and closing balances, transaction reconstruction, debit/credit
normalization, source evidence, and account-type-aware reconciliation.

The Wells Fargo business line-of-credit processor uses layout-aware PDF
evidence where column position carries transaction direction. This is an
intentional example of the package treating PDF layout as source
evidence when flattened text alone is insufficient to preserve financial
meaning.

## American Express Support

American Express support was introduced for `0.5.0` and remains included
in `0.10.0`.

Supported account families are:

``` text
personal credit card
business credit card
business checking
business line of credit
personal loan
```

The complete American Express private archive currently validates:

``` text
692 / 692 PASS
reconciliation=PASS
difference=0.00
```

The archive includes statement evidence spanning 2013 through 2026 and
covers multiple historical layouts and extraction grammars.

American Express credit-card support reconstructs payments, credits,
charges, fees, and interest while preserving source context such as
card-ending sections and supported continuation detail.

Business checking support normalizes deposit-account activity and uses
asset-account reconciliation:

``` text
opening balance
+ credits
- debits
= closing balance
```

Business line-of-credit and personal-loan support use debt-account
reconciliation:

``` text
opening balance
+ debits
- credits
= closing balance
```

The personal-loan work introduced first-class `LOAN` account support to
the generic domain rather than encoding loan semantics as a special case
inside one processor.

## Discover Checking Support

Discover checking statements are handled through:

``` text
discover.checking.v1
```

The processor has been validated against two private account archives
totaling 200 monthly statements:

``` text
200 / 200 PASS
reconciliation=PASS
difference=0.00
```

Observed statement formats span 2018 through 2026.

The supported archive includes the evolution from:

``` text
CASHBACK CHECKING
```

to:

``` text
CASHBACK DEBIT
```

and the transition from legacy `DiscoverBank.com` statement branding to
current `Discover.com` branding.

The processor supports:

``` text
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

``` text
Eff. Date
Bus. Date
```

and later:

``` text
Eff. Date
Syst. Date
```

The normalized transaction date uses the statement's posting/system date
when available because that is the date Discover identifies as the date
the transaction is generally processed and posted.

## Discover Credit Card Support

Discover credit-card statements are handled through:

``` text
discover.credit_card.v1
```

The private Discover credit-card archive currently validates:

``` text
70 / 70 PASS
reconciliation=PASS
difference=0.00
```

Observed formats span 2019 through 2025.

Two major statement grammars are supported.

Legacy statements expose separate transaction and posting dates:

``` text
Trans. Date
Post Date
```

Newer statements expose a single transaction-date column.

For legacy statements, the normalized transaction date prefers the
reported posting date. For newer statements, the reported transaction
date is resolved relative to the statement closing date. This
intentionally allows statement activity whose printed transaction date
precedes the nominal billing-period start when the statement itself
reports that activity in the current cycle.

Supported economic activity includes:

``` text
payments and credits
purchases
fees
interest
```

Fee and interest activity is normalized from the statement's period
totals. This avoids double-counting when the same interest amount is
also broken out by interest category elsewhere in the statement.

The processor also tolerates a proven PDF extraction artifact where text
from an adjacent rewards column can appear after a complete transaction
amount. That adjacent-column text is preserved in raw source evidence
but is not silently appended to the transaction description.

## Capital One Credit Card Support

Capital One consumer credit-card statements are handled through:

``` text
capital_one.credit_card.v1
```

The private Capital One consumer credit-card archive currently
validates:

``` text
38 / 38 PASS
reconciliation=PASS
difference=0.00
```

Observed Venture X statement formats span 2023 through 2026.

The processor supports:

``` text
statement identity and billing periods
opening and closing balances
cardholder-scoped payments and credits
purchases
fees
interest
transaction and posting dates
foreign-currency continuation detail
cross-year transaction-date resolution
```

For dated activity, the normalized transaction date prefers the
statement's reported posting date. This matches the account's
billing-cycle behavior, including transactions whose transaction date
precedes the nominal statement period but whose posting date falls
inside the current cycle.

Foreign-currency detail such as the original amount, currency code, and
exchange rate is preserved in raw source evidence without being silently
appended to the merchant description.

Fee rows are independently checked against the statement's reported
period fee total. Interest is normalized once from the statement's
period total so category detail does not create duplicate economic
activity.

## Capital One Business Credit Card Support

Capital One business credit-card statements are handled through:

``` text
capital_one.business_credit_card.v1
```

The private business credit-card archive currently validates:

``` text
86 / 86 PASS
reconciliation=PASS
difference=0.00
```

That corpus consists of:

``` text
Spark
    82 / 82 PASS

Venture X Business
    4 / 4 PASS
```

Observed formats span 2019 through 2026.

The processor supports multiple proven historical grammars within the
same Capital One business-card family.

Legacy Spark statements can flatten two visual transaction columns into
one physical extracted-text line. The processor reconstructs the
independent date-led transaction segments before normalization rather
than treating the flattened line as one activity record.

Current Spark and Venture X Business statements use
transaction/post-date activity tables. Both remain inside the same
processor because the corpus demonstrates a common business credit-card
family with explicit product-aware grammar boundaries.

Venture X Business statements may omit interest sections entirely. The
parser does not invent missing interest behavior and instead requires
only the sections proven for the matched product grammar.

## Capital One Checking Support

Capital One 360 Checking statements are handled through:

``` text
capital_one.checking.v1
```

The private checking archive currently validates:

``` text
75 / 75 PASS
reconciliation=PASS
difference=0.00
```

The corpus contains two private 360 Checking accounts and includes both
monthly and quarterly reporting behavior.

Supported behavior includes:

``` text
full account identity
statement-period parsing
monthly statement periods
quarterly 90/91/92-day statement periods
beginning and ending balances
deposits and credits
withdrawals and debits
transfers
wrapped transfer descriptions
reference-token continuation lines
zero-activity statements
cross-year transaction dates
running-balance validation
```

Capital One checking rows expose a running balance. The processor uses
that reported balance as an additional parser invariant: reconstructed
activity must produce the exact balance transition reported by the
statement before the normalized statement reaches package-level
reconciliation.

This provides two independent checks:

``` text
transaction row
    → running-balance validation

complete statement
    → asset-account reconciliation
```

The two observed account archives share the same 360 Checking grammar,
so they are handled by one processor rather than duplicated
account-specific implementations.

## PenFed HELOC Support

PenFed home-equity line-of-credit statements are handled through:

``` text
penfed.heloc.v1
```

The private PenFed HELOC archive currently validates:

``` text
25 / 25 PASS
reconciliation=PASS
difference=0.00
```

Observed statement formats span 2024 through 2026.

The processor supports statement identity, reporting periods, opening
and closing balances, principal curtailment payments, payment receipts,
returned payments, NSF reversals, returned-check fee activity, and cycle
finance charges.

PenFed HELOC activity contains multiple bookkeeping views of the same
payment. A received payment can be accompanied by a separate allocation
row showing how that payment was applied to interest or principal. The
processor distinguishes actual economic activity from allocation detail
so payments are not double-counted.

Returned-payment cycles are handled explicitly. Fee assessments, fee
reversals, principal or interest reversals, replacement payments, and
other recognized activity are normalized according to their effect on
the debt balance rather than inferred from the summary totals.

Two proven activity-table grammars are supported. Earlier statements
expose a single transaction date, while the current observed layout
exposes separate process and effective dates. These layouts remain
within one processor because the corpus demonstrates a stable PenFed
HELOC statement family with an explicit grammar boundary.

Finance charges are parsed from the statement's finance-charge section
and participate in debt-account reconciliation. Summary values remain
independent validation checkpoints rather than substitutes for
transaction activity.

## U.S. Bank Business Checking Support

U.S. Bank business checking statements are handled through:

``` text
us_bank.business_checking.v1
```

The private Silver Business Checking archive currently validates:

``` text
35 / 35 PASS
reconciliation=PASS
difference=0.00
```

Observed statement formats span 2023 through 2026.

The processor supports statement identity and reporting periods,
beginning and ending balances, deposits, withdrawals, `Other Deposits`,
`Other Withdrawals`, analysis service charges, wrapped transaction
descriptions and reference detail, zero-activity statements, negative
balances, compact extracted dates, and cross-year transaction dates.

Economic direction follows the deposit account's perspective:

``` text
balance-increasing activity
    → CREDIT

balance-decreasing activity
    → DEBIT
```

Summary labels are distinguished from actual transaction-section headers
so account-summary bookkeeping is not mistaken for economic activity.
Analysis service charges are normalized as dated withdrawals when the
statement reports them as real account activity.

## U.S. Bank Credit Card Support

U.S. Bank credit-card statements are handled through:

``` text
us_bank.credit_card.v1
```

The private U.S. Bank credit-card archive currently validates:

``` text
70 / 70 PASS
reconciliation=PASS
difference=0.00
```

Observed statement formats span 2019 through 2026 and include historical
Radisson Rewards Visa branding, Altitude Go Visa Signature, and Platinum
Visa.

These products remain inside one processor because the private corpus
demonstrates a common U.S. Bank credit-card grammar. Product branding is
source evidence rather than a processor boundary.

The processor supports:

``` text
Activity Summary balance checkpoints
Payments and Other Credits
Purchases and Other Debits
Fees
fee reversals and credits
Interest Charged
Other Debits
merchant returns and statement credits
multi-page transaction continuation
zero-dollar fee rows
cross-year transaction dates
legacy and current account-number wording
```

Debt-increasing purchases, fees, interest, and other debits normalize as
`DEBIT`. Payments, refunds, statement credits, and fee reversals
normalize as `CREDIT`. Transaction amounts remain positive magnitudes.

The processor independently validates transaction-section totals exposed
by the statement before package-level reconciliation. This prevents
silent row loss or duplication from appearing successful merely because
a statement was recognized.

Fees and interest are normalized only from their proven economic
sections. Zero-dollar fee rows are accepted as statement bookkeeping
without inventing economic activity. Repeated transaction headings on
continuation pages preserve the active transaction family across page
boundaries.

Historical product branding changed during the archive, but the
underlying statement grammar remained compatible. Processor ownership
therefore follows document structure rather than card-product names.

## Statement Balances

Supported statements expose generic balance checkpoints:

``` python
StatementBalanceSummary(
    opening_balance=...,
    closing_balance=...,
)
```

These values are parsed as stated by the bank. They are not rewritten to
force reconciliation.

A parser is responsible for understanding the statement grammar.
Reconciliation then independently verifies whether normalized economic
activity explains the reported balance movement.

## Reconciliation

Reconciliation is optional and separate from parsing.

``` python
from banking_statements.reconciliation import reconcile_statement

result = reconcile_statement(statement)
```

Reconciliation is account-type aware.

For debt accounts such as credit cards, lines of credit, and loans:

``` text
opening balance
+ parsed debits
- parsed credits
= expected closing balance
```

For asset accounts such as checking and savings:

``` text
opening balance
+ parsed credits
- parsed debits
= expected closing balance
```

The result includes parsed debit and credit totals, expected closing
balance, difference, and a `reconciled` boolean. A mismatch does not
rewrite the parsed statement.

The private archive smoke tooling is stricter by default and treats a
reconciliation mismatch as a smoke failure so incomplete or misdirected
activity is surfaced during development.

Reconciliation is therefore not a parser shortcut. It is an independent
validation layer used to prove that the extracted financial activity is
economically complete.

## Financial Values

Financial values use `Decimal`.

``` python
from decimal import Decimal

from banking_statements import to_decimal

assert to_decimal("123.45") == Decimal("123.45")
assert to_decimal("$1,234.56") == Decimal("1234.56")
assert to_decimal("(42.17)") == Decimal("-42.17")
```

Floating-point arithmetic is intentionally avoided for normalized
financial values.

Normalized transaction amounts use positive magnitudes. Economic
direction is represented separately by `TransactionDirection`.

## Source Evidence

Normalized statement data should remain traceable to the source
statement.

``` python
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

``` text
source file identity
page
section
raw text
processor
sequence
```

This provenance is important for auditing parser behavior, debugging
future statement revisions, and verifying reconciliation decisions.

## Architecture

The implemented processing pipeline is:

``` text
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

``` text
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

``` python
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

Processors should be narrow enough that previously proven behavior
remains stable as the package grows.

A materially different statement structure should generally receive a
new processor rather than turning an existing processor into an
increasingly broad universal parser.

Multiple proven historical layouts can remain inside one processor when
they belong to the same statement family and can be distinguished
explicitly without weakening the processor's failure behavior.

## Institution Detection

Institution detection uses explicit marker signatures derived from
observed statement evidence.

A signature should be specific enough to identify the institution
without claiming unrelated documents from the same company.

Institution detection and processor selection are separate steps:

``` text
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

New signatures should be added because an observed document requires
them, not because a broader marker seems theoretically convenient.

## Deterministic Processor Selection

`ProcessorRegistry` requires exactly one compatible processor.

``` text
0 matches
    → UnsupportedStatementError

1 match
    → selected

2 or more matches
    → AmbiguousProcessorError
```

There is intentionally no "first matching processor wins" behavior.

Processor registration order must not silently resolve ambiguous
statement formats.

## Development Philosophy

The central maintenance rule is:

> Proven behavior stays stable.

When a future statement fails, the failure should first be classified.

``` text
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

The package should grow as a library of proven document grammars rather
than as one parser that attempts to understand every possible statement.

## Strict Failure Policy

A parser success should mean that the known statement grammar was
understood.

The package should not silently discard or guess around:

``` text
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

Specific failures are preferred over generic parse errors because they
make future statement support easier to develop and audit.

The normal development response to a new archive failure is to inspect
the evidence first, not to make the parser broadly more permissive.

## Logical Rows

PDF extraction often does not produce one physical line per financial
transaction.

Real statements may contain:

``` text
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

``` text
physical extracted lines
    ↓
logical statement rows
    ↓
economic normalization
```

This keeps layout reconstruction separate from transaction
interpretation.

## Institution Support

Current implemented support:

``` text
Chase
    credit card
    business credit card
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

Capital One
    credit card
    business credit card
    checking

PenFed
    home-equity line of credit

U.S. Bank
    business checking
    credit card
```

A bank, account family, or statement format is listed as supported only
after its processor has been implemented and validated against real
statement evidence.

The complete private development archive currently contains 2381
supported statements, all of which pass extraction, institution
detection, processor selection, parsing, normalization, and strict
reconciliation with zero difference.

## Private Statement Corpus

Real financial statements used during development are maintained outside
the repository.

The expected local structure is:

``` text
private-data/
└── statements/
    ├── chase/
    ├── wellsfargo/
    ├── american-express/
    ├── discover/
    ├── capitalone/
    ├── penfed/
    ├── usbank/
    └── ...
```

`private-data/` is excluded from Git.

Real statements, account numbers, transaction histories, names,
addresses, transaction references, balances, and other private financial
data must never be committed to the repository or distributed in package
artifacts.

Public tests use generic synthetic statement data.

Synthetic fixtures should preserve only the structural grammar required
to prove parser behavior. They should never copy real names, account
numbers, addresses, merchant references, transaction identifiers,
balances, or other private values from the development archive.

## Statement Inspection

Development includes tooling for inspecting the exact text extracted
from a PDF statement.

``` bash
make inspect-statement \
    file="private-data/statements/example/statement.pdf"
```

Inspect a specific page:

``` bash
make inspect-statement \
    file="private-data/statements/example/statement.pdf" \
    page=2
```

Optionally limit displayed text:

``` bash
make inspect-statement \
    file="private-data/statements/example/statement.pdf" \
    head=3000
```

Parser behavior should be developed against the text actually returned
by the package's PDF extraction layer rather than assumptions based only
on how a PDF looks visually.

## Archive Smoke Testing

Institution processors are validated against private historical
statement archives.

The development workflow is intentionally chronological:

``` text
01 PASS
02 PASS
03 PASS
04 FAIL
```

Development stops at the first failure.

That statement is inspected, the failure is classified from actual
extracted evidence, and the smallest correct capability or grammar
extension is added.

A generic synthetic regression test is then added before the archive
resumes.

Typical usage:

``` bash
make smoke-archive \
    folder="private-data/statements/example"
```

Resume from a particular archive position:

``` bash
make smoke-archive \
    folder="private-data/statements/example" \
    from=4
```

Limit the run:

``` bash
make smoke-archive \
    folder="private-data/statements/example" \
    limit=10
```

Continue after failures when mapping an archive:

``` bash
make smoke-archive \
    folder="private-data/statements/example" \
    continue=1
```

A strict smoke PASS means:

``` text
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

``` bash
uv run python -m scripts.archive_smoke \
    private-data/statements/example/statement.pdf \
    --show-transactions
```

Allow reconciliation mismatches for investigation without turning them
into smoke failures:

``` bash
uv run python -m scripts.archive_smoke \
    private-data/statements/example \
    --allow-reconciliation-failures
```

Include a traceback while investigating:

``` bash
uv run python -m scripts.archive_smoke \
    private-data/statements/example/statement.pdf \
    --show-transactions \
    --allow-reconciliation-failures \
    --traceback
```

The private corpus is a local integration and regression corpus. It is
never a source of public fixture data.

## Development Workflow for New Statement Families

A new account family is developed from evidence rather than from
assumptions.

The typical loop is:

``` text
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

For a bounded account family, development may begin with one
comprehensive investigation capture that includes the relevant processor
source, synthetic tests, integration points, and extracted text for the
complete private corpus. Additional investigation captures should target
specific structural uncertainties exposed by the first pass rather than
repeating the complete corpus.

This front-loads grammar discovery without changing the evidence
standard. U.S. Bank is a concrete example: two investigation passes were
enough to map two account-family processors across 105 statements before
implementation, and the complete private corpus then validated 105 / 105
with zero reconciliation difference.

Private statements remain local evidence only; public repository tests
continue to use generic synthetic data.

Whether development proceeds chronologically or from a bounded corpus
map, changes are still made at the smallest proven grammar boundary.

The goal is not merely to make every PDF parse. The goal is to
understand why each supported statement reconciles.

## Development

Install development dependencies:

``` bash
uv sync --dev
```

Format:

``` bash
make format
```

Check formatting:

``` bash
make format-check
```

Lint:

``` bash
make lint
```

Type check:

``` bash
make typecheck
```

Run tests:

``` bash
make test
```

Run tests in parallel:

``` bash
make test-fast
```

Run branch coverage:

``` bash
make coverage
```

The project maintains:

``` text
100% branch coverage
```

## Quality Gates

Run the normal validation suite:

``` bash
make check
```

Run the CI-equivalent validation pipeline:

``` bash
make ci
```

Before preparing a release:

``` bash
make release-check
```

The release check validates:

``` text
formatting
linting
mypy
100% branch coverage
distribution build
distribution metadata
typed wheel contents
clean-wheel installation
```

A release should also be smoke-validated against the complete supported
private archive before publication.

## Build

Build the source distribution and wheel:

``` bash
make build
```

Validate distributions:

``` bash
make check-dist
```

Inspect wheel contents:

``` bash
make wheel-contents
```

Install the built wheel into a clean environment:

``` bash
make install-wheel
```

The distributed wheel includes:

``` text
banking_statements/py.typed
```

so type information is available to downstream type checkers.

## Dependency Management

The project uses `uv`.

Synchronize the development environment:

``` bash
make sync
```

Refresh the lockfile:

``` bash
make lock
```

Upgrade dependencies:

``` bash
make upgrade
```

`uv.lock` is committed so CI and local release validation can use
reproducible locked environments.

After changing package metadata or dependencies, refresh the lockfile
before committing when required:

``` bash
uv lock
```

## Python Support

Supported Python versions:

``` text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

CI validates the full supported version matrix.

## Typing

`banking-statements` is a typed package.

The project uses strict mypy checking during development:

``` bash
make typecheck
```

The wheel includes the PEP 561 marker:

``` text
banking_statements/py.typed
```

## Scope

The package is intentionally narrow.

It aims to provide:

``` text
bank statement parsing
statement normalization
source and layout evidence
processor selection
strict statement validation
account-type-aware reconciliation
typed Python domain objects
```

It does not aim to provide:

``` text
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

Those concerns can consume the normalized statement objects produced by
this package without becoming responsibilities of the statement parser
itself.

## Roadmap

Current milestone:

``` text
0.10.0
    seven-institution statement support

    Chase
        credit card
        business credit card
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

    Capital One
        credit card
        business credit card
        checking

    PenFed
        home-equity line of credit

    U.S. Bank
        business checking
        credit card

    account-type-aware reconciliation
    layout-aware PDF evidence
    strict institution detection
    deterministic processor selection
    running-balance validation where exposed by statement evidence
    100% branch coverage
    2381 / 2381 private statements PASS
```

Next evidence-driven institution target:

``` text
To be selected from the next private statement corpus.
```

Expected later phases:

``` text
additional account families for supported institutions
additional institutions
additional historical statement grammars
additional reconciliation capabilities when required by statement evidence
```

The roadmap is evidence-driven.

Modules and abstractions should be added because real statement formats
require them, not because they appear theoretically useful.

## Contributing

Contributions are welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting
changes.

The most important contribution rule is:

> New evidence should extend the system at the smallest correct boundary
> without destabilizing previously proven processors.

Never include real private financial statements or personally
identifiable financial information in issues, pull requests, tests, or
commits.

## Security

Please report security issues according to [SECURITY.md](SECURITY.md).

Do not disclose private financial information or credentials in public
security reports.

## License

`banking-statements` is released under the MIT License.

See [LICENSE](LICENSE) for details.
