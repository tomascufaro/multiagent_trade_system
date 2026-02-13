# Agent instructions

## Communication

- **Be concise.** Answer only what is asked. Omit filler, preambles, and "I understand" / "Sure" style replies.
- **Be clear.** Prefer short, direct sentences. One idea per sentence when it helps.
- **Minimize verbosity.** No long explanations unless the user asks. No restating the question back. No step-by-step narration when a single block of changes suffices.

## Scope and edits

- **Do only what is requested.** Do not add features, refactors, or "improvements" that were not asked for.
- **No unnecessary edits.** Do not change formatting, names, or structure in files you are not explicitly asked to modify. Do not suggest unrelated cleanups.
- **No redundant comments.** Do not add comments that restate what the code does. Add comments only when they explain non-obvious why or constraints.
- **No irrelevant content.** Do not add docs, README updates, or extra files unless the user asks for them.

## Code and behavior

- **Preserve existing behavior.** When editing, keep current logic and APIs unless the request explicitly changes them.
- **One concern per change.** Prefer a single, focused edit over many scattered tweaks.
- **Verify before stating.** Do not assert facts about the codebase without checking. Prefer reading the file over guessing.

Keep this file short. Prefer adding a single explicit rule over long paragraphs. Update only when a recurring mistake appears.
