# Contributing to CRAFT

Thank you for your interest in contributing to CRAFT! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/CRAFT.git
   cd CRAFT
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e ".[all,dev]"
   ```

4. **Set Up Pre-commit Hooks** (optional but recommended)
   ```bash
   pre-commit install
   ```

## Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

3. **Run Tests**
   ```bash
   pytest
   ```

4. **Format Code**
   ```bash
   black craft/
   ruff check craft/
   ```

5. **Type Check**
   ```bash
   mypy craft/
   ```

6. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

7. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Examples:
```
feat: add ChromaDB vector store adapter
fix: resolve streaming issue in OpenAI provider
docs: update installation instructions
test: add tests for conversation memory
```

## Code Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use Black for formatting
- Use Ruff for linting

## Testing

- Write tests for all new features
- Maintain or improve code coverage
- Run the full test suite before submitting PR

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=craft --cov-report=html

# Run specific test file
pytest tests/test_chatbot.py
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all functions and classes
- Include type hints
- Provide examples for new features

## Pull Request Process

1. **Update Documentation**: Ensure README and docstrings are updated
2. **Add Tests**: All new code should have tests
3. **Pass CI**: Ensure all CI checks pass
4. **Describe Changes**: Provide clear PR description
5. **Link Issues**: Reference related issues

## Areas for Contribution

### High Priority
- [ ] Vector store adapters (ChromaDB, Pinecone, FAISS)
- [ ] Embedding providers
- [ ] Database adapters (SQLite, PostgreSQL, Redis)
- [ ] REST API implementation
- [ ] MCP server/client

### Medium Priority
- [ ] Additional LLM providers (Cohere, Ollama)
- [ ] Web widgets (JavaScript, React)
- [ ] Analytics and metrics
- [ ] Rate limiting

### Low Priority
- [ ] Documentation improvements
- [ ] Example applications
- [ ] Performance optimizations
- [ ] Additional tests

## Questions?

Feel free to:
- Open an issue for discussion
- Join our community discussions
- Ask in your PR

Thank you for contributing! 🎉
