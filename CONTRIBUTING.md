# Contributing to ChatMind

Thank you for your interest in contributing to ChatMind! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Issues

- **Bug reports**: Use the [GitHub Issues](https://github.com/yourusername/chatmind/issues) page
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

- Python 3.8+
- Node.js 16+
- Neo4j Database
- OpenAI API Key

### Local Development

1. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/chatmind.git
   cd chatmind
   ```

2. **Set up environment**
   ```bash
   pip install -r requirements.txt
   cp env.example .env
   # Edit .env with your credentials
   ```

3. **Install frontend dependencies**
   ```bash
   cd chatmind/frontend
   npm install
   cd ../..
   ```

4. **Test the pipeline**
   ```bash
   # Add test data
   cp test_data.zip data/raw/
   python run_pipeline.py
   ```

## 📝 Code Style

### Python
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints where appropriate
- Add docstrings for functions and classes
- Keep functions focused and reasonably sized

### JavaScript/TypeScript
- Follow the existing code style
- Use TypeScript for new components
- Add JSDoc comments for functions
- Use meaningful variable and function names

### General
- Write clear, descriptive commit messages
- Add tests for new functionality
- Update documentation for new features
- Keep changes focused and atomic

## 🏗️ Project Structure

### Backend (Python)
- **chatmind/**: Main package
  - **data_ingestion/**: ChatGPT export processing
  - **embedding/**: Semantic clustering
  - **tagger/**: AI-powered tagging
  - **neo4j_loader/**: Graph database loading
  - **api/**: FastAPI backend

### Frontend (React/TypeScript)
- **chatmind/frontend/**: React application
  - **src/components/**: React components
  - **src/hooks/**: Custom React hooks
  - **src/types/**: TypeScript type definitions

### Data
- **data/**: User data (not in repository)
- **docs/**: Documentation
- **scripts/**: Utility scripts

## 🧪 Testing

### Running Tests
```bash
# Python tests
python -m pytest tests/

# Frontend tests
cd chatmind/frontend
npm test
```

### Test Data
- Use the provided test data in `test_data.zip`
- Don't commit personal ChatGPT exports
- Create minimal test cases for new features

## 📚 Documentation

### Updating Documentation
- Update `README.md` for major changes
- Update `docs/UserGuide.md` for user-facing changes
- Add inline comments for complex code
- Update API documentation for backend changes

### Documentation Standards
- Use clear, concise language
- Include code examples where helpful
- Keep documentation up to date with code changes
- Use consistent formatting and style

## 🚀 Release Process

### Before Submitting a PR
1. **Test thoroughly**: Run the full pipeline with test data
2. **Check for breaking changes**: Ensure existing functionality still works
3. **Update documentation**: Add docs for new features
4. **Update requirements**: Add new dependencies to `requirements.txt`
5. **Test installation**: Try a fresh install from your fork

### Review Process
- All PRs require review before merging
- Maintainers will review code quality, tests, and documentation
- Address feedback and make requested changes
- Keep PRs focused and reasonably sized

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment details**: OS, Python version, Node.js version
2. **Steps to reproduce**: Clear, step-by-step instructions
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Error messages**: Full error output if applicable
6. **Sample data**: Minimal example that reproduces the issue

## 💡 Feature Requests

When requesting features, please include:

1. **Problem description**: What problem does this solve?
2. **Proposed solution**: How should it work?
3. **Use cases**: Who would benefit from this?
4. **Alternatives considered**: What other approaches were considered?

## 📄 License

By contributing to ChatMind, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You

Thank you for contributing to ChatMind! Your contributions help make this tool better for everyone. 