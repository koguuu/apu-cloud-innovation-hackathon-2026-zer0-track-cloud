# How we work (5 people, 6 days)

## Branch and pull request flow

1. **Never push straight to `main`.**
2. Update first: `git checkout main && git pull`
3. Make your own branch: `git checkout -b yourname/short-feature` (e.g. `raja/wifi-probes`)
4. Commit small and often, with clear messages.
5. Push your branch: `git push -u origin yourname/short-feature`
6. Open a **Pull Request** on GitHub into `main`.
7. Tag a teammate to check it. Keep reviews fast (same day).
8. After it's checked, **merge** it. Then everyone runs `git pull` on `main`.

## Rules

- Tell the group before you edit a file someone else owns.
- Only change the shared data contract ([docs/event-schema.md](docs/event-schema.md)) after telling everyone, because many people depend on it.
- **No secrets in git.** API keys go in `.env` (ignored). Only `.env.example` is committed.
- Feature freeze: **8 Nov**. After that, only fixes, polish, deck and demo video.

## Commit messages

Short and clear: `add AP fault injection script`, `fix ticket JSON field name`.
