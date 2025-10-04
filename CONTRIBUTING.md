# Contributing to mobile-use 🚀

Hey there, contributor! 🎉 First off, thank you for considering helping out with mobile-use. Every contribution, big or small, is incredibly valuable to us.

## 🏁 Getting Started

Ready to dive in? Here’s how you can get set up:

1.  **Fork & Clone**: Fork the repository and clone it to your local machine.
2.  **Set Up Your Environment**: Follow the "Manual Launch (Development Mode)" instructions in our `README.md` to get everything installed and ready to go.

## 💻 How to Contribute

Got an idea or a fix? Here’s the general workflow:

1.  **Pick an Issue**: A great place to start is our issues tab. Look for anything tagged `good first issue`!
2.  **Create a Branch**: Create a descriptive branch name for your feature or bug fix.
    ```bash
    git checkout -b your-awesome-feature
    ```
3.  **Write Your Code**: This is the fun part! Make your changes and improvements.
4.  **Keep It Clean**: Before you commit, make sure your code is formatted and linted correctly with Ruff.

    ```bash
    # Check for any linting errors
    ruff check .

    # Automatically format your code
    ruff format .
    ```

5.  **Run Tests**: Make sure all the tests pass with `pytest`.
    ```bash
    pytest
    ```
6.  **Commit Your Changes**: Use clear and descriptive commit messages. We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard.

## ✨ Submitting a Pull Request

When your code is ready, open a Pull Request!

- Push your branch to your fork.
- Open a PR against the `main` branch of the original repository.
- Make sure all the tests pass with `pytest`.
- Provide a clear description of the changes you've made. We'll review it as soon as we can!

## 📦 Dependency Management with `uv`

We use [`uv`](https://github.com/astral-sh/uv) to manage our dependencies. It's fast, and efficient.

### Installing Dependencies

To get all the project dependencies installed from the lockfile, just run:

```bash
uv sync
```

This ensures your environment is perfectly aligned with ours.

### Adding a New Package

Need to add a new package? Here’s how:

```bash
# For a production package
uv pip install <package-name>

# For a development-only package
uv pip install <package-name> --extra=dev
```

After installing, don't forget to update the lockfile and commit the changes:

```bash
uv lock
# git add uv.lock pyproject.toml && git commit ...
```

That's it! Thanks again for your contribution. We're excited to see what you build!

## 🛡️ Quality Guardrails

This repo uses pre-commit hooks and CI gates to keep code quality and security high.

- Install hooks:
  ```
  uv sync --all-extras --dev
  pre-commit install
  ```
- Run hooks locally:
  ```
  pre-commit run --all-files
  ```
- Hooks include:
  - ruff (lint + import rules, auto-fix)
  - black (format check)
  - basic text checks (trailing whitespace, EOF)
  - optional gitleaks (requires the `gitleaks` binary on PATH)

CI (GitHub Actions) runs:
- Lint, format check, tests + coverage, package build
- Security: dependency-review (PRs), Trivy filesystem scan, pip-audit, CodeQL
