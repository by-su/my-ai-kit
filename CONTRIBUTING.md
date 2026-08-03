# Contributing

Thanks for helping improve my-ai-kit.

## Workflow

1. Create a feature branch from `main`.
2. Keep commits scoped to one reviewable change.
3. Run validation before opening a pull request:

```bash
python3 -m unittest discover -s tests
python3 -m py_compile bin/mykit src/*.py adapters/*.py
```

4. Open a pull request with a clear summary and verification notes.

## Commit Style

Use Conventional Commits:

```text
feat: add a user-visible feature
fix: correct a bug
docs: update documentation only
chore: update metadata, generated files, or maintenance tasks
refactor: restructure code without behavior changes
test: add or update tests
ci: update CI configuration
```

Do not force-push `main` after the repository is public. Rebase and squash only on your own feature branches.
