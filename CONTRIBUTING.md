# Contributing to Unified Docs Hub

Thank you for your interest in contributing to Unified Docs Hub! This document provides guidelines for contributing to the project.

## How to Contribute

### Adding New Repositories

The most common contribution is adding high-quality repositories to our curated list:

1. Fork the repository
2. Edit `repositories.yaml` to add your repository
3. Follow the format:

```yaml
- repo: "owner/repository-name"
  category: "Appropriate Category"
  description: "Clear, concise description of what the repo does"
  quality_score: 8  # 1-10, based on documentation quality
  priority: 1      # 1-3, based on importance
  doc_paths:
    - "docs/"
    - "README.md"
    - "documentation/"
  topics: ["relevant", "tags", "here"]
```

#### Quality Score Guidelines

- **10**: Exceptional documentation with tutorials, examples, API references
- **8-9**: Comprehensive documentation with good examples
- **6-7**: Good basic documentation
- **4-5**: Minimal but usable documentation
- **1-3**: Poor documentation (rarely included)

### Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Reporting Issues

- Use GitHub Issues to report bugs
- Include Python version, OS, and full error messages
- Provide steps to reproduce the issue

### Feature Requests

- Open a GitHub Issue with the "enhancement" label
- Describe the feature and its use case
- Discuss implementation approach if you have ideas

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/unified-docs-hub.git
cd unified-docs-hub

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest
```

## Code Style

- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and modular

## Testing

- Add tests for new features
- Ensure all tests pass before submitting PR
- Test with different Python versions if possible

## Documentation

- Update README.md if adding new features
- Add docstrings to new functions
- Include examples in documentation

## Pull Request Process

1. Update README.md with details of changes if needed
2. Ensure all tests pass
3. Update version numbers if applicable
4. PR will be merged after review and approval

Thank you for contributing!
