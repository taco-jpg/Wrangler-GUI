# Contributing to Wrangler Desktop

Thank you for your interest in contributing!
This document explains how to get involved.

## Ways to Contribute

- **Report bugs** — Open a bug report issue with detailed steps to reproduce
- **Suggest features** — Open a feature request issue with your use case
- **Submit pull requests** — Fix bugs or implement new features
- **Improve documentation** — Fix typos, add examples, improve clarity
- **Platform testing** — Test on Windows or Linux and report issues

## Getting Started

### Prerequisites
- Python 3.13+
- Node.js & npm
- wrangler CLI (`npm install -g wrangler`)

### Local Setup
```bash
git clone https://github.com/taco-jpg/Wrangler-GUI.git
cd Wrangler-GUI
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Submitting a Pull Request

1. Fork the repository
2. Create a feature branch:
   `git checkout -b fix/your-fix-name`
   or
   `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test that `python main.py` starts without errors
5. Commit with a clear message:
   `git commit -m "fix: description of what you fixed"`
6. Push and open a Pull Request against the `main` branch

## Good First Issues

New to the project? Look for issues labeled
[`good first issue`](https://github.com/taco-jpg/Wrangler-GUI/issues?q=is%3Aissue+label%3A%22good+first+issue%22)

Current areas that need help:
- Windows and Linux platform compatibility
- JavaScript syntax highlighting in the code editor
- Cross-platform keyboard shortcuts (Cmd → Ctrl on Windows)
- Unit tests

## Code Style

- Follow the conventions in `CLAUDE.md`
- Use snake_case for functions and variables
- Use PascalCase for class names
- Keep colors and fonts in `ui/theme.py` — no hardcoded values
- All GUI updates must happen on the main thread

## Commit Message Format

Use the following prefixes:
- `fix:` — bug fixes
- `feat:` — new features
- `docs:` — documentation changes
- `refactor:` — code refactoring
- `test:` — adding tests
- `chore:` — maintenance tasks

## Platform Support

Wrangler Desktop is developed and tested on macOS.
Windows and Linux support is a work in progress.
If you're testing on other platforms, your feedback is especially valuable.

## Questions?

Open an issue with the `question` label —
we're happy to help you get started.