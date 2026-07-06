# Humanizer checklist

Distilled from [github.com/blader/humanizer](https://github.com/blader/humanizer): a
catalog of the specific patterns that make prose read as AI-generated, and what
to do instead. Apply this as an explicit editing pass *after* content is drafted
— write first, then sweep every chapter against this list before calling it done.
The premise: LLMs default to the statistically most likely phrasing, and that
phrasing has recognizable tells. None of these are hard grammar rules; they're
a fingerprint, and readers increasingly notice it.

## Content issues

1. **Significance inflation.** "a pivotal moment in the evolution of X" → say what
   actually happened, with a specific fact.
2. **Notability name-dropping.** Lists of outlets/companies as a substitute for a
   sourced claim ("featured in TechCrunch, Forbes, and Wired") → cite the actual
   claim with a real source instead of the appearance of authority.
3. **Superficial -ing analyses.** "symbolizing," "reflecting," "showcasing" used to
   gesture at meaning without committing to it → say the specific thing, or cut it.
4. **Promotional language.** "breathtaking," "game-changing," "seamless" → neutral,
   specific description. If it's actually fast, say how fast, measured how.
5. **Vague attributions.** "experts believe," "many developers report" → name the
   source or drop the claim. This course's whole premise is grounded claims.
6. **Formulaic challenges.** "despite challenges, X continues to thrive" → the
   actual challenge and the actual outcome, concretely.

## Language misuse

7. **AI vocabulary.** Notice when these appear and mean nothing extra: "testament,"
   "landscape," "leverage" (as a verb), "delve," "boast," "crucially," "notably,"
   "robust," "seamless." Usually deletable with no loss of meaning — try it.
8. **Copula avoidance.** "serves as," "functions as," "acts as" where "is" would do.
9. **Negative parallelisms.** "It's not just X, it's Y" — say Y. If X matters too,
   say both plainly; the rhetorical inversion is a tic, not an insight.
10. **Rule of three.** Don't pad a list to exactly three items because it sounds
    complete. Two is fine. Four is fine. Use the number that's actually true.
11. **Synonym cycling.** Repeating the clearest term is better than rotating
    synonyms to avoid "repetition" — that instinct makes technical writing worse,
    since precision matters more than variety.
12. **False ranges.** "from X to Y" used as a rhetorical framing device rather than
    an actual range → list the actual things.
13. **Passive voice / subjectless fragments** where naming the actor would be
    clearer. ("Mistakes were made" energy.)

## Style problems

14. **Em/en dash overuse.** The single most common tell. Most em-dashes can become
    a period, a comma, a colon, or parentheses. Reserve dashes for the rare case
    where none of those work as well. (This course caught ~260 of these across 12
    chapters in one pass — see how naturally the phrasing above the checklist
    entry could have used one.)
15. **Boldface overuse**, especially the "**Term** — description" inline-header
    list pattern repeated across several bullets. Convert to flowing prose;
    reserve bold for genuine table/definition-list terms.
16. **Inline-header lists.** Same issue as #15 — a bulleted list where every item
    starts "**X**: explanation" reads as generated. Prose paragraphs read as written.
17. **Title Case Headings** where sentence case is the house style (check what
    the rest of the book does and match it).
18. **Emojis** in prose. Exception: deliberate UI iconography (this course's own
    callout-box icons — ⚠ 🏭 🔬 ⚡ — are a designed component of the layout, not
    decorative flourish, and should stay).
19. **Curly quotes** where the rest of the document uses straight quotes (or
    vice versa) — pick one and stay consistent.
20. **Chatbot artifacts.** "I hope this helps! Let me know if you have any
    questions." has no place in a book chapter.
21. **Cutoff disclaimers.** "While details are limited..." → go find the details,
    or scope the claim to what you actually verified.
22. **Sycophantic tone.** "Great question!" energy pointed at an imagined reader.
23. **Filler phrases.** "in order to" → "to". "due to the fact that" → "because".
    "at this point in time" → "now".
24. **Excessive hedging.** "could potentially possibly" → "may". Say what you mean
    at the confidence level you actually have.
25. **Generic conclusions.** A chapter shouldn't end on "In conclusion, X is a
    powerful tool" — end on the specific next action (this course's "Try it" box
    already does this structurally; don't undercut it with a vague summary above it).
26. **Hyphenated word pairs** dropped where the unhyphenated form is standard
    ("data-driven" → "data driven" is often fine; check house style).
27. **Persuasive authority tropes.** "At its core, what matters is..." → state
    the claim directly.
28. **Signposting announcements.** "Let's dive in," "Here's what you need to
    know" → just start. The heading already signposts the section.
29. **Fragmented headers** that need a restating sentence right under them
    ("Performance. This section is about performance.") → let the heading stand
    and get straight to content.
30. **Diff-anchored writing.** Describe what something does and why, not what
    changed from a previous version of the code/doc you were looking at — that
    context won't exist for the reader.
31. **Manufactured punchlines.** Staccato drama like "No config. No boilerplate.
    No surprises." → vary sentence length naturally instead of imitating a trailer.
32. **Aphorism formulas.** A neat-sounding maxim standing in for a real claim →
    replace with the actual claim.
33. **Conversational rhetorical openers.** "Honestly? It depends." as a fake-candid
    setup → just answer the question.

## How to run this pass

1. Read each chapter's prose (not the code blocks) end to end.
2. Grep for the cheap, mechanical signals first: em-dashes (`—`), the words
   "crucially," "leverage," "testament," "landscape," "delve," "boast," "seamless,"
   "robust," curly quotes, and `<strong>` density per chapter. Fix what a regex
   can find before doing the close read — it's faster and catches most of the volume.
3. Do one close read per chapter for the harder-to-grep patterns: negative
   parallelism, rule-of-three padding, arrow-chain constructions ("If X → Y → Z"),
   signposting, generic conclusions.
4. Re-render the page and re-read it once more. Cadence matters as much as any
   individual rule — a chapter that's technically pattern-free can still read
   stiffly if every sentence is the same length and shape.
5. Never let this pass change a technical claim's meaning. This is a style edit,
   not a content edit — if fixing the prose reveals the underlying claim was
   vague or unverified, that's a research gap, not a humanizing job. Flag it and
   go verify it instead of smoothing over it.
