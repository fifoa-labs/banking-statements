# Security Policy

## Supported Versions

Security fixes are provided for the latest released version of this project.

Older releases may not receive security updates.

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues, discussions, pull requests, or other public channels.

Instead, use GitHub's private vulnerability reporting feature for this repository when available.

When submitting a report, please include enough information to reproduce and evaluate the issue, such as:

* a clear description of the vulnerability
* affected versions or commits
* reproduction steps
* proof-of-concept code or sample input, when appropriate
* the potential security impact
* any suggested mitigation or fix

Please avoid including real credentials, private financial information, personally identifiable information, access tokens, account numbers, or other sensitive data in reports unless absolutely necessary.

## Response Process

Security reports will be reviewed and triaged based on severity, reproducibility, and impact.

When a vulnerability is confirmed, maintainers may:

* develop and test a fix privately
* prepare a patched release
* publish a security advisory
* coordinate disclosure with the reporter when appropriate

Public disclosure should occur only after a reasonable opportunity has been provided to investigate and address the issue.

## Security Expectations

Contributors should avoid introducing patterns that unnecessarily increase security risk, including:

* hard-coded credentials or secrets
* unsafe deserialization
* arbitrary code execution from untrusted input
* insecure temporary-file handling
* unnecessary shell execution
* logging or exposing sensitive information
* committing private or production data
* disabling security checks without a documented reason

Dependencies should be kept minimal and updated when security fixes require it.

## Sensitive Data

Never commit sensitive data to the repository.

This includes, but is not limited to:

* passwords
* API keys
* access tokens
* private keys
* financial account information
* personally identifiable information
* production configuration
* private documents or datasets

Use synthetic or appropriately sanitized data in tests and examples.

If sensitive information is accidentally committed, removing it in a later commit may not be sufficient because it can remain in Git history. Revoke or rotate affected credentials immediately and remove the information from repository history where appropriate.

## Scope

This policy covers vulnerabilities in the project's source code, distributed packages, build and release configuration, and project-controlled automation.

Security issues in third-party dependencies should generally be reported to the maintainers of those dependencies, unless the project's use of the dependency introduces an additional vulnerability.
