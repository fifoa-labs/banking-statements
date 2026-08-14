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

Version `0.1.0` establishes the package foundation: typed statement and
transaction domain objects, source-evidence models, page-aware text models,
financial `Decimal` normalization, processor contracts, and deterministic
processor selection.

No specific bank statement format is claimed as supported in `0.1.0`.
Institution-specific processors will be added only after they have been
developed and validated against real statement evidence.

The package intentionally focuses on answering:

> What did this bank statement say?

It is not a budgeting application, bank API client, accounting system,
merchant-categorization engine, personal finance manager, tax engine, database
layer, or Beancount-specific importer.

* **PyPI:** https://pypi.org/project/banking-statements/
* **Source:** https://github.com/fifoa-labs/banking-statements
* **License:** MIT

## Current Status

`banking-statements` is currently in early development.

The `0.1.0` release provides the generic architecture required to build strict,
institution-specific bank statement processors without coupling the package to
a single bank or statement layout.

Current foundation:

```text
banking-statements 0.1.0

Python
    3.11
    3.12
    3.13
    3.14

Domain
    StatementSource
    SourceEvidence
    StatementPeriod
    ParsedStatement
    TransactionEvent
    TransactionDirection

Financial values
    Decimal-based normalization

Text
    StatementPage
    StatementText
    StatementTextReader

Processors
    ProcessorMatch
    StatementProcessor
    ProcessorRegistry

Validation
    deterministic processor selection
    explicit unsupported-statement failure
    explicit ambiguous-processor failure

Quality
    Ruff
    mypy strict
    pytest
    100% branch coverage
```

Institution-specific statement support will be documented only after a processor
has been validated against a meaningful private historical corpus.

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

The initial public package exposes generic domain and processor primitives.

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

The package does not yet expose a default bank-specific parser in `0.1.0`.

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

The intended processing pipeline is:

```text
PDF
    ↓
page-aware text extraction
    ↓
institution detection
    ↓
processor selection
    ↓
statement structure
    ↓
logical transaction rows
    ↓
focused economic parsing
    ↓
normalized domain objects
    ↓
strict validation
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

`banking-statements` is intended to support multiple U.S. banking institutions.

Future processor families may include institutions such as:

```text
Bank of America
Chase
U.S. Bank
Wells Fargo
Capital One
other U.S. banks
```

This list represents intended package scope, not current support.

A bank or statement format should be listed as supported only after its
processor has been implemented and validated against real statements.

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

A future smoke-test PASS should mean:

```text
document extraction succeeded
institution detection succeeded
processor selection succeeded
required statement structure was understood
recognized financial rows were accounted for
normalized output validated
unsupported activity was not silently discarded
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
source evidence
processor selection
strict statement validation
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

The next development phases are expected to be:

```text
0.1.x
    generic package foundation
    page-aware PDF extraction
    institution detection
    statement inspection tooling
    private archive smoke tooling

first institution milestone
    first real bank detector signature
    first statement processor
    statement identity parsing
    statement-period parsing
    logical transaction rows
    normalized transactions
    real archive validation

later milestones
    additional statement revisions
    additional institutions
    statement-level validation
    possible reconciliation capabilities
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
