# Publishing to PyPI

This guide explains how to publish the No-Code ADK package to PyPI so that users can install it with pip.

## Prerequisites

1. Create a PyPI account at https://pypi.org/account/register/
2. Install required tools:
   ```bash
   pip install --upgrade build twine
   ```

## Building the Package

1. Run the build script:
   ```bash
   python build_package.py
   ```

   This will create distribution files in the `dist/` directory.

2. Check the distribution files:
   ```bash
   ls dist/
   ```

   You should see both `.tar.gz` (source distribution) and `.whl` (wheel) files.

## Testing the Package Locally

Before publishing to PyPI, you can test the package locally:

```bash
pip install --editable .
```

Then try running:

```bash
adk-nocode start
```

## Publishing to PyPI

1. Upload to PyPI Test (optional, for testing):
   ```bash
   python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
   ```

2. Upload to PyPI:
   ```bash
   python -m twine upload dist/*
   ```

   You'll be prompted for your PyPI username and password.

3. Verify the package is available:
   - Visit https://pypi.org/project/google-adk-nocode/
   - Try installing it: `pip install google-adk-nocode`

## Updating the Package

To update the package:

1. Update the version number in `pyproject.toml`
2. Run the build script again
3. Upload to PyPI

## Troubleshooting

- If you get an error about the package already existing, make sure you've updated the version number.
- If you have authentication issues, you can create an API token in your PyPI account settings and use that instead of your password.
- For more detailed information, see the [Python Packaging User Guide](https://packaging.python.org/tutorials/packaging-projects/).
