# Size the job

Recommend a size with one line of reasoning, then let the user confirm or switch. Use a tappable question tool if the harness has one.

- **Small:** one or two sittings, one area of the code or one document, no new data model, easy to undo. Examples: a bug fix, a settings screen, one email sequence. Gets `summary.md` only, plus screenshots if there is a screen to check.
- **Big:** several sessions, new features or data, several areas of the code, or a customer is waiting on it. Examples: a new module for a customer app, a site redesign, a new product. Gets a PRD, phases, and a review for every phase.

When unsure, recommend big. A big plan that turns out short costs little; a small plan that turns out big goes off the rails.

Write the confirmed size into the `Size` line of `summary.md`.
