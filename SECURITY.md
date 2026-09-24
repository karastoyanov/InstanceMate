# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities privately using [GitHub Security Advisories](../../security/advisories/new) for this repository. Do not open a public issue for security reports.

We'll acknowledge your report and work with you on assessment, a fix, and coordinated disclosure.

## Scope

Areas of particular concern for InstanceMate:

- **Credential handling** — how ServiceNow login credentials (OAuth tokens, basic auth), LLM provider API keys (BYOK), and session data are stored, transmitted, and scoped.
- **Instance access** — anything that could allow the assistant to read or act beyond what the authenticated user is authorized to see or do on their ServiceNow instance.
- **Prompt injection via instance data** — ServiceNow records (incidents, KB articles, descriptions, comments, etc.) are untrusted input. Content returned from an instance should never be able to make the assistant take unintended actions, exfiltrate data, or escalate privileges.

## Design principle: read-only against instances

InstanceMate is designed to be **read-only** against connected ServiceNow instances. The MCP server should not expose tools that create, update, or delete instance data unless that capability has been explicitly and deliberately added with its own review and safeguards. Reports of tools or code paths that perform unexpected writes are treated as security issues.
