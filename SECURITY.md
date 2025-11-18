# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of CRAFT seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please do NOT:

- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it has been addressed

### Please DO:

1. **Email us directly** at [INSERT SECURITY EMAIL]
2. **Include in your report:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
   - Your contact information

### What to expect:

- **Acknowledgment**: We will acknowledge your email within 48 hours
- **Updates**: We will send you regular updates about our progress
- **Timeline**: We aim to patch critical vulnerabilities within 7 days
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices

When using CRAFT in production:

### API Keys

- **Never hardcode API keys** in your code
- Use environment variables or secure key management systems
- Rotate keys regularly
- Use different keys for development and production

```python
# ✅ Good
import os
api_key = os.getenv("ANTHROPIC_API_KEY")

# ❌ Bad
api_key = "sk-ant-api-key-here"
```

### Input Validation

- **Sanitize user inputs** before processing
- Implement rate limiting to prevent abuse
- Validate and sanitize all data from external sources

### Storage Security

- **Encrypt sensitive data at rest** when using storage adapters
- Use strong database passwords
- Restrict database access to authorized services only
- Enable SSL/TLS for database connections

```python
# PostgreSQL with SSL
storage = PostgreSQLStorage(
    host="db.example.com",
    database="craft",
    username="craft_user",
    password=os.getenv("DB_PASSWORD"),
    ssl_mode="require"  # Enforce SSL
)
```

### API Security

- **Use HTTPS** in production
- Implement authentication (API keys, OAuth)
- Enable rate limiting
- Validate all API inputs
- Use CORS appropriately

```python
# API with authentication
from craft.integrations.api import CRAFTServer, APIKeyManager

api_keys = APIKeyManager()
api_key = api_keys.create_key(name="production", rate_limit=100)

server = CRAFTServer(
    chatbot=chatbot,
    api_key_manager=api_keys,
    enable_cors=True,  # Configure CORS properly
)
```

### Dependency Security

- Keep dependencies up to date
- Regularly run security audits:
  ```bash
  pip install safety
  safety check
  ```
- Use dependabot or similar tools for automatic updates

### Logging Security

- **Don't log sensitive information** (API keys, passwords, PII)
- Use structured logging with sanitization
- Implement log retention policies

```python
# ✅ Good - No sensitive data
logger.info("User chat", user_id="user-123", message_length=50)

# ❌ Bad - Logs sensitive content
logger.info("User chat", api_key=api_key, message=user_message)
```

### Production Deployment

- Use a reverse proxy (nginx, Caddy) for HTTPS termination
- Implement proper firewall rules
- Use container security scanning for Docker images
- Enable audit logging
- Implement monitoring and alerting

## Known Security Considerations

### LLM-Specific Risks

1. **Prompt Injection**: Users may attempt to manipulate the system prompt
   - Mitigation: Validate and sanitize inputs, use system prompts wisely

2. **Data Leakage**: LLMs might inadvertently reveal training data
   - Mitigation: Don't include sensitive data in prompts

3. **Cost Attacks**: Malicious users might generate expensive requests
   - Mitigation: Implement rate limiting and cost monitoring

### RAG-Specific Risks

1. **Data Poisoning**: Malicious documents in vector store
   - Mitigation: Validate documents before indexing, implement access controls

2. **Prompt Leaking**: Retrieval might expose sensitive document content
   - Mitigation: Implement document access controls, sanitize retrieved content

## Security Updates

We will publish security advisories for:

- Critical vulnerabilities (CVSS >= 7.0)
- High vulnerabilities affecting production deployments
- Vulnerabilities with known exploits

Subscribe to security updates:
- Watch this repository
- Check GitHub Security Advisories
- Follow release notes in CHANGELOG.md

## Compliance

CRAFT aims to support common security and compliance requirements:

- **GDPR**: Support for data deletion and export
- **SOC 2**: Audit logging and access controls
- **HIPAA**: Encryption at rest and in transit (when configured)

Note: Compliance depends on how you deploy and configure CRAFT.

## Security Checklist

Before deploying to production:

- [ ] API keys stored securely (environment variables or key vault)
- [ ] HTTPS enabled
- [ ] Authentication implemented
- [ ] Rate limiting configured
- [ ] Input validation in place
- [ ] Logging configured (without sensitive data)
- [ ] Database connections encrypted
- [ ] Dependencies up to date
- [ ] Security audit completed
- [ ] Monitoring and alerting configured
- [ ] Backup and disaster recovery plan
- [ ] Incident response plan documented

## Contact

For security concerns: [INSERT SECURITY EMAIL]

For general questions: [GitHub Issues](https://github.com/StefanoHernandez/CRAFT/issues)

---

**Last Updated**: 2025-01-18

Thank you for helping keep CRAFT and our users safe!
