# Contributing to PrintOscar Backend

Thank you for your interest in contributing! 🎉

## Development Setup

1. Fork & clone: `git clone https://github.com/YOUR_USERNAME/print_oscar_backend.git`
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Install deps: `pip install -r requirements.txt`
4. Setup DB (see README)
5. Run: `scripts/run_dev.ps1`

## Workflow

```
git checkout -b feat/add-user-avatar
git commit -m "feat: add user avatar upload and resizing"
git push origin feat/add-user-avatar
# Create PR
```

## Code Standards

- Black + Ruff formatting (`ruff check --fix`, `black .`)
- Type hints with mypy
- 100% test coverage for new features
- Docstrings for public APIs

## Commit Messages

```
feat: add user avatar upload endpoint
fix: resolve cart quantity validation edge case
docs: update payment gateway docs
refactor: extract payment router service
chore: update deps
```

## Testing

```bash
pytest  # Unit tests
pytest tests/integration/  # API tests
```

## Pull Request Checklist

- [ ] Tests pass
- [ ] Linting passes (`ruff check`, `black --check`)
- [ ] Docs updated
- [ ] Changes covered by tests (80%+)
- [ ] No breaking changes (or deprecation path)

## Issues

- 🐛 Bug reports: Describe reproduction steps
- 🚀 Feature requests: Explain user value + implementation thoughts

Happy coding! 🚀
