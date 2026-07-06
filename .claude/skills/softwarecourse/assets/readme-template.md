# {{COURSE_TITLE}}

<!--
  One to two sentences. State the topic, the version/API style targeted,
  and the "why trust this" angle (real infra, real tests) if one exists.
  Read as the opening line of a course landing page, not a package
  description — a stranger should know in one sentence whether this is
  for them.
-->
{{ONE_TO_TWO_SENTENCE_TAGLINE}}

<!--
  ONE badge, not two. {{PAGES_URL}} / {{PAGES_HOST_PATH}} only resolve once
  the repo is deployed, so leave them as literal tokens until Deploy step 7
  (same family of tokens the book itself uses in its sidebar — see
  index-template.html/chapter-template.html).

  The book is the single source of truth for "how do I get an environment,"
  not the README — every chapter already has its own Launch-Codespace link
  and its own local-setup instructions in the Try It box. Don't duplicate a
  second Codespaces badge here; it drifts out of sync with the book and,
  the one time this was tried, left a dangling "click the badge above" once
  someone simplified the README later and forgot the badge was load-bearing
  for that sentence. One badge means there's nothing to keep in sync.

  Build the "Read the Book" badge as a shields.io badge matching the book's
  own brand color, so it doesn't look like a generic placeholder shield:
  https://img.shields.io/badge/📖_Read_the_Book-{{PAGES_HOST_PATH}}-{{BRAND_HEX}}
  {{BRAND_HEX}} is the course's own --brand CSS variable (no leading "#")
  and is already known at stage 3 — fill it in immediately, it doesn't wait
  for Deploy. {{PAGES_HOST_PATH}} is the Pages host+path with no scheme,
  e.g. "adamontherun.github.io" or "adamontherun.github.io/sqlalchemy-mastery"
  if the Pages URL has a path segment — spaces become underscores, and a
  literal "-" inside a label must be escaped as "--" or shields.io reads it
  as a field separator.
-->
[![Read the Book](https://img.shields.io/badge/📖_Read_the_Book-{{PAGES_HOST_PATH}}-{{BRAND_HEX}})]({{PAGES_URL}})

<!--
  Screenshot of the book's cover page, captured and linked back to the book
  during Deploy step 8 — see SKILL.md for the capture/crop/compress
  procedure. {{SCREENSHOT_PATH}} is typically
  `book/assets/screenshots/homepage.png`. Write real alt text describing
  what's actually visible (cover copy, sidebar TOC, etc.), not "screenshot".
-->
[![{{SCREENSHOT_ALT_TEXT}}]({{SCREENSHOT_PATH}})]({{PAGES_URL}})

<!--
  This paragraph exists because a reader landing on the repo (not the book)
  has no way to know these are two different things with two different
  audiences. Say it plainly. Adapt "terminal with Postgres already running"
  to whatever this course's environment actually provides — a REPL, a
  running dev server, nothing at all if there's no live infra (in which
  case say "a terminal with the toolchain already installed" instead).
-->
This repo is two things: **the book** ({{CHAPTER_COUNT}} chapters of prose,
nothing to install) and **the code** (runnable examples and failing-test
challenges, which need an environment). Every chapter in the book links
straight back to Codespaces, so you're never more than one click from
{{WHAT_S_ALREADY_RUNNING}}.

## What's covered

<!--
  One bullet per PART, not per chapter — a visitor should see the shape of
  the course in five seconds without opening the book. Pull the part
  titles/summaries straight from book/index.html's toc-parts section so
  this never drifts out of sync with the actual table of contents.
-->
- **Part {{PART_ROMAN}} · {{PART_TITLE}}** — {{ONE_LINE_PART_SUMMARY}}

## Setup

<!--
  Codespaces gets one sentence that points at the book, not a repeated
  badge/instructions block — see the note on the badge above for why.
  If stage 1 decided this topic needs live infrastructure, keep the local
  path below as-is. If the topic is self-contained (no Docker/Compose file
  exists), drop the "environment" language and reduce this to whatever the
  ecosystem's own one-line install command is (uv sync / npm install /
  cargo build / etc.).
-->
Don't want to install anything? Open [the book]({{PAGES_URL}}) and click
"Launch Codespace" in any chapter's sidebar — it opens a cloud dev
environment with {{WHAT_S_ALREADY_RUNNING}}.

To run locally, you need {{PREREQUISITE_TOOLS_WITH_LINKS}}:

```sh
{{SETUP_COMMANDS}}
```

{{ANY_LOCAL_INFRA_NOTES — e.g. port numbers, credentials, why a non-default
port was chosen. Delete this paragraph if there's nothing non-obvious to say.}}

## Doing challenges

Every chapter has a challenge under `challenges/`: a skeleton file with
failing tests. Edit the skeleton until the tests pass:

```sh
{{CHALLENGE_RUN_COMMAND}}
```

Reference solutions live in `solutions/`. No peeking until the tests pass.

<!--
  Only include this section if the topic has live infra that accumulates
  state examples/challenges don't already clean up after themselves.
  Delete it entirely for self-contained topics.
-->
## Resetting the database

Examples clean up after themselves, but if you ever want a pristine database:

```sh
{{RESET_COMMAND}}
```
