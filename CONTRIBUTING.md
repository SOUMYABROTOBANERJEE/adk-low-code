# Contributing to No-Code ADK

Thank you for your interest in contributing to No-Code ADK! This document provides guidelines and instructions for contributing to this project.

## Setting Up Development Environment

### Prerequisites

- Python 3.9 or higher
- Git

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/abhishekkumar35/google-adk-nocode.git
   cd google-adk-nocode
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
   This will install the package in development mode with all the development dependencies (pytest, black, flake8, etc.).

4. Run the application locally:
   ```bash
   python app.py
   ```

## Development Workflow

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and test them locally.

3. Ensure your code follows the project's style guidelines.

4. Update documentation if necessary.

5. Commit your changes with a descriptive commit message:
   ```bash
   git commit -m "Add feature: your feature description"
   ```

6. Push your branch to GitHub:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Create a pull request on GitHub.

## Building and Testing

### Building the Package

To build the package locally:

```bash
python -m build
```

### Testing

Run tests with:

```bash
pytest
```

## Code Style Guidelines

- Follow PEP 8 guidelines for Python code
- Use descriptive variable and function names
- Add docstrings to functions and classes
- Keep functions small and focused on a single task

## Documentation

- Update the README.md file with any new features or changes
- Add docstrings to new functions and classes
- Update the example code if necessary

## Releasing

The release process is handled by the maintainers. If you think a new release is needed, please open an issue.

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [Apache License 2.0](LICENSE).
