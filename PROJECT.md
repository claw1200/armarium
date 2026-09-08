# Armarium

A private sample library browser. The full collection lives on a NAS; devices only keep copies of samples actually used in a project.

## Vision

Browse a large remote library as if it were local. When a sample is used, the client downloads a real file and that local copy is what the DAW receives. No full-library sync.

The desktop client is the product (cache + OS drag into a DAW). A web UI may later offer browse/preview only. It is not required for MVP.

## Design

The filesystem on the server is the source of truth. A catalog database stores metadata for fast browse; it never stores audio bytes.

**Local cache:** downloads recreate the server folder path under a user cache root, keeping original filenames.

```
~/Armarium/cache/Drums/Kicks/kick.wav
```

Same basename in different folders do not collide. Files stay readable in the DAW. Content-hash renaming is rejected: unique names, unreadable in the project. Deduplication is deferred. If added later, prefer a client-side hash after download (“already have this audio”) over hashing and rewriting the whole server library.

Preview uses HTTP range requests so audition does not require a full download. Drag into a DAW is enabled only after the local file is complete.

LAN-first. Remote-over-internet (auth, VPN) is later.

## Architecture

One repo, two apps. Client and server ship on different cadences but share an API, so they stay in the same tree. Separate repos would only add contract drift.

| Piece | Choice | Role |
|---|---|---|
| Server | Python 3, FastAPI, Docker Compose | Index library, serve catalog + audio |
| Catalog | SQLite | Paths, size, mtime, cheap audio metadata |
| Client | Tauri 2 + Svelte 5 | Browse, preview, download, native file drag |
| Library mount | Read-only volume | NAS files, not copied into the DB |

```
armarium/
  PROJECT.md
  AGENTS.md
  compose.yml          # server (+ later browse-only web)
  server/              # FastAPI app, indexer, Dockerfile
  client/              # Svelte UI
    src-tauri/         # Rust: cache, downloads, native drag
```

The Svelte UI is the desktop frontend and, later, the optional website. Native work stays in `src-tauri`. No shared package until the API contract needs one (OpenAPI from FastAPI is enough).

Indexer: periodic scan first; live watch later. Waveforms and heavy analysis are on-demand, not a full-library import.

## Quality

Linters and tests ship with the first code, and run on every PR and on `master`. Configured lint rules must pass 100%; disagreements go in the linter config (e.g. no forced Python docstrings), not as ignored failures.

Unit tests are useful; they are not the whole suite. Add integration coverage from the start, automated. Test code follows the same quality bar as production. Prefer fewer tests that really exercise a behaviour over broad, low-value cases.

Coverage is a tripwire early (do not let it drop) — not a score to maximise later.

## Features

**MVP (now)** — folder browse, catalog scan, ranged preview, download into a mirrored cache path, drag the local file into a DAW. Built in six testable slices:

1. **Drag proof** — Tauri shell drags a fixture wav into another app.
2. **Catalog API** — Dockerized scan + folder/file listing.
3. **Ranged audio** — stream/download by catalog id, HTTP 206.
4. **Browse + preview** — Svelte UI against the API (browser is enough).
5. **Cached download** — Tauri writes `{cacheRoot}/{serverRelativePath}/{filename}`.
6. **Use in project** — drag the cached file only; download first if missing.

**Next** — filename search, on-demand waveforms, simple cache management, browse-only web UI, live reindex, client-side hash dedup.

**Later / ideas** — tags and collections, BPM/key, similarity, cache size caps, multi-user, mobile, internet access. Not in scope until the drag-to-DAW loop works.
