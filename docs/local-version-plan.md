# Local single-user version — conversion plan

Target: one person runs this on their own computer; it opens in the browser; all data
stays local; extraction uses local Ollama. See `AGENTS.md` for the binding rules.
Hosted/multi-user code is preserved on branch `archive/hosted-multiuser`.

## Keep (do not touch — these are correct / still needed)

- `app/income/*` — the income math engine. Pure, deterministic, ties out to the
  worksheets to the cent. **Untouched.**
- `app/schemas/*` — input/result models (`ScheduleCYear`, `ExtractedField`, etc.). The
  contract the extractor fills.
- `app/parsers/*` — still needed to get text/images out of PDFs to feed the model.
- `app/services/extraction_service.py` — keep the `extract_fields(...)` signature; only
  its internals change.
- `tests/tieout/*` and the Excel oracle — the income regression net.
- The case/document/result models and repositories (minus the multi-user columns).
- The UI / frontend — review screen, click-to-source. Update only what auth touched.

## Remove (exists only because it was hosted/multi-user)

- `app/routers/auth.py`, JWT logic, login — no auth in a single-user local app.
- `app/models/user.py`, `user_role.py`, `borrower_role.py`(role parts), and any
  `broker_id` / per-user ownership filtering in services and repositories.
- Manager vs broker role checks everywhere.
- Railway / Postgres deployment config, Procfile worker entry, `nixpacks.toml` cloud
  bits. Keep a simple local run path instead.

## Simplify

- **Postgres → SQLite.** Default `database_url` to a local SQLite file; drop Postgres
  driver from the default path. The repo already runs on SQLite for tests, so this is
  mostly config + removing Postgres assumptions.
- **Separate worker process → in-process background thread.** A history commit already
  runs the worker in-process with local storage; make that the only path. Delete
  `worker_main.py` / the standalone worker entry.
- **Config defaults that "just work."** Ollama URL (`http://localhost:11434`), model
  name, storage path, SQLite path — all sensible defaults, zero required env vars.

## Add (new for the local app)

1. **Local launcher.** One command starts Uvicorn on localhost and opens the browser
   (e.g. `python -m app`). Document in README: install deps, install Ollama, `ollama pull <model>`, run.
2. **Ollama extractor** behind `extract_fields(...)`: send parsed text + a fixed JSON
   schema to local Ollama (temperature 0), parse structured fields into `ExtractedField`
   with a `confidence`.
3. **Arithmetic validation layer.** Reconcile extracted numbers against the form's own
   math; flag failures for review instead of using them silently.
4. **`confidence` on `ExtractedField`** + a review flag the UI can surface.

## Suggested order (each step shippable + tested)

1. Branch + archive (below). Get the app starting locally on SQLite with the worker
   in-process. (No behavior change yet — just the local runtime.)
2. Rip out auth + multi-user scoping. App still works, now with no login.
3. Local launcher + README "pull and run" instructions.
4. Ollama extractor behind the existing interface (start with `tax_return`).
5. Arithmetic validation + review flags.
6. Prove it on the two Hendrickson returns end-to-end → expect **$7,988.33**.

## Git: save-point + new branch (run on YOUR machine, not the sandbox)

The sandbox can't run git here (locked index + cloud-sync). On your computer:

```bash
# from the repo, on a clean main
git checkout main
git pull

# preserve the current hosted/multi-user version
git branch archive/hosted-multiuser
git push -u origin archive/hosted-multiuser

# start the local version
git checkout -b local-app

# remove a stray scratch file left in the repo root
git rm --cached run_engine.py 2>/dev/null; rm -f run_engine.py

git add AGENTS.md docs/local-version-plan.md docs/verification docs/prompts
git commit -m "Redirect to single-user local app; archive hosted version"
git push -u origin local-app
```

Now "the guy" pulls `local-app` (or `main` once you merge) and runs the start command.
