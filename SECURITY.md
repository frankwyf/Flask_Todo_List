# Security Policy

## Supported Versions
This project is maintained on the latest `main` branch.

## Reporting a Vulnerability
Please open a private security report through GitHub Security Advisories when
possible.

If private reporting is not available, open an issue with minimal details and
mark it clearly as security-related. Do not include exploit code or secrets in
public reports.

## Secret Handling
- Never commit credentials, API keys, or `.env` files.
- Use `.env.example` as a template.
- Rotate any leaked credential immediately.
