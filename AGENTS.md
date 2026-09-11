# Agent instructions

Read `PROJECT.md` before changing product behaviour, cache layout, or scope.

Write DRY, self-documenting code. Names, function shape, and file layout should make comments unnecessary. Prefer types (Python annotations, TypeScript) over docstrings and inline explanation. Do not add comments that restate the code.

Prefer a correct design over a local patch. When something is wrong, ask whether the approach is wrong, not only whether a line is.

Do not keep outdated designs, docs, or agent instructions. Cut bloat in code, documentation, and this file.

## UI

Prefer native daisyUI classes and browser primitives (`popover`, `<dialog>`, `<details>`). Do not wrap library open/close in JS state.

Themes are `armarium-light` (default) and `armarium-dark` (`prefers-color-scheme`). Surfaces: page canvas is `bg-base-200`; navbar, sidebar, cards, and the player are `bg-base-100` with `border-base-300`. Nested wells inside a card use `bg-base-200`. Floating menus are `bg-base-100` plus a hairline border.

Sidebar matches the console drawer: `menu` (not `menu-sm`), labels hide when collapsed (`is-drawer-close:hidden`), width `w-14` / `w-64`. Do not bind `open` on submenu `<details>`.

Icons are Lucide via `icon-[lucide--…]`. Icon-only chrome needs `aria-label`. Shared empty/error: `EmptyState` and `ErrorBanner`. List pages live in `$lib/pages`; routes stay thin. Canonical library page: `LibraryPage.svelte`.
