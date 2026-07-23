# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.4.x   | Yes       |
| < 0.4   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability within PRSPNSD, please send an email to
**[INSERT EMAIL]**. All security vulnerabilities will be promptly addressed.

**Please do NOT report security vulnerabilities through public GitHub issues.**

### What to Include

When reporting a vulnerability, please include:

1. Description of the vulnerability
2. Steps to reproduce the issue
3. Potential impact
4. Suggested fix (if any)

### Response Expectations

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours.
- **Assessment**: We will assess the vulnerability within 5 business days.
- **Fix**: We will work on a fix and aim to release a patch within 14 days for
  critical vulnerabilities.
- **Disclosure**: We will coordinate with you on the timing of public disclosure.

### Scope

This security policy applies to:

- The `reachq` Python package
- The GitHub repository and CI/CD pipeline
- Documentation and example code

### Out of Scope

- Vulnerabilities in third-party dependencies (report these to the respective
  maintainers)
- Issues that require physical access to the user's machine
- Social engineering attacks

## Security Best Practices

When using PRSPNSD in production:

1. **Pin dependencies**: Use `requirements.txt` or lock files to pin exact versions.
2. **Use virtual environments**: Isolate project dependencies.
3. **Run in sandboxed environments**: Don't run untrusted graph inputs with
   elevated privileges.
4. **Validate inputs**: While our algorithms handle arbitrary graphs, ensure
   input data is validated before processing.
5. **Monitor dependencies**: Use tools like `pip-audit` or GitHub Dependabot to
   track vulnerabilities in dependencies.

## Dependency Security

We use GitHub Dependabot to monitor dependencies for known vulnerabilities.
If you discover a vulnerability in a dependency:

1. Check if a patched version is available
2. Update the dependency in `pyproject.toml`
3. Test the update thoroughly
4. Submit a PR with the fix

## Code Security

This library performs computational operations on graphs. While there are no
network-facing components, be aware of:

- **Memory usage**: Large graphs may consume significant memory. Set appropriate
  limits when processing untrusted input.
- **Computation time**: Some algorithms have superlinear time complexity. Set
  timeouts when processing untrusted input.
- **Numerical precision**: Floating-point operations in shortest path algorithms
  may have precision limitations for very large or very small values.
