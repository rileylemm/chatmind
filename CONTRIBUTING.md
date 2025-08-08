# Contributing to ChatMind

Thank you for your interest in contributing to ChatMind! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Issues

- **Bug reports**: Use the GitHub Issues page
- **Feature requests**: Create an issue with the "enhancement" label
- **Documentation**: Report documentation issues or suggest improvements

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Test your changes**: Ensure the pipeline still works
5. **Commit your changes**: Use clear, descriptive commit messages
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Create a Pull Request**: Provide a clear description of your changes

## 🧪 Development Setup

### Prerequisites

- Python 3.10+
- Node.js 20+
- Docker (for Neo4j/Qdrant)

### One-time setup
```bash
# Install pre-commit hooks (optional but recommended)
pipx install pre-commit || pip install pre-commit
pre-commit install

# Install mkdocs (optional, for docs)
pip install mkdocs-material
```

### Local Development

```bash
# Start databases (root compose)
docker compose up -d neo4j qdrant

# Run pipeline (local models)
chatmind --local

# Start API
cd chatmind/api && python run.py

# Start frontend
cd chatmind/frontend && npm install && npm run dev
```

## 📝 Code Style

### Python
- Use ruff/black formatting (pre-commit will auto-fix)
- Add type hints where appropriate

### JavaScript/TypeScript
- ESLint + Prettier (configured in frontend)
- Use TypeScript for new components

## 📚 Documentation

- Update `README.md` for major changes
- Update `docs/` (mkdocs) for detailed docs
- Add/adjust examples for new features

## 📄 License

By contributing to ChatMind, you agree that your contributions will be licensed under the Apache License 2.0.

## 🙏 Thank You

Thank you for contributing to ChatMind! Your contributions help make this tool better for everyone. 