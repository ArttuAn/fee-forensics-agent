# Security Policy

## Supported Versions

| Version | Supported |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2.0 | :x: |

## Reporting a Vulnerability

If you discover a security vulnerability in Fee Forensics, please report it responsibly.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please send an email to the project maintainer at the contact information available in the repository.

### What to Include

Please include as much of the following information as possible:

- A description of the vulnerability
- Steps to reproduce the vulnerability
- Affected versions
- Potential impact
- Any suggested fixes or mitigations

### Response Timeline

- **Initial response**: Within 48 hours
- **Detailed response**: Within 7 days
- **Fix release**: As soon as feasible, depending on severity

### Disclosure Policy

We follow responsible disclosure practices:

1. Acknowledge receipt of the report within 48 hours
2. Work with the reporter to understand and validate the issue
3. Develop and test a fix
4. Release a security update
5. Coordinate public disclosure with the reporter

## Security Best Practices

When using Fee Forensics:

- **Never commit sensitive data**: Do not include real bank statements or personal financial information in the repository
- **Review output carefully**: Always review the generated reports before sharing
- **Keep dependencies updated**: Regularly update dependencies to get security patches
- **Use environment variables**: Store API keys and sensitive configuration in environment variables, not in code

## Dependency Security

This project uses:

- `pip-audit` in CI/CD to check for known vulnerabilities in dependencies
- `bandit` in CI/CD for static security analysis of Python code

## License

This project is licensed under the MIT License - see the LICENSE file for details.
