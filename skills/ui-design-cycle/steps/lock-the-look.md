# Lock the look

These questions sit inside the `bm-prd-creator` interview that `cycle-orchestration` runs for a big cycle. Ask them as part of feature scoping for the "shared look" feature, or just before it. One decision at a time, each with a recommendation and one line of why, using a tappable question tool when the harness has one. Write each answer into `summary.md` Decisions as it is made.

## The questions

1. **Which screens first?** Recommend: every screen a regular user sees first, admin or back-office screens after, to match. Users and prospects see the user side; admins tolerate rough edges longer.
2. **Font.** If the documented target is a paid font (Avenir, Proxima Nova and similar), say it needs a web license, name the free font already in use or a close free match, and recommend keeping the free one unless the user already owns the license.
3. **Colors.** If the code's colors drift from the documented brand (an older gold, pure black text), recommend moving to the brand values, with near-black kept only for dark chrome (status bars, PWA theme color). Softer text color is easier to read.
4. **Shape.** Corner radius and button style. Follow the brand reference (the public website is usually the north star). State the limit as a rule, for example "no corner larger than rounded-lg".
5. **Dark mode.** Say what the code does today. Recommend keeping the current mode and leaving dark mode for a later cycle unless it is the point of the job; it doubles every color decision and every screenshot.
6. **Shared brands.** If several brands share the styles, confirm the change applies to all of them and that every check covers each one.
7. **Out of scope.** Propose the standard cuts: new features or behavior changes, native app screens, form fields and legal wording, generated PDFs and emails, animations and illustrations, new logos, the marketing site. Confirm.

If the user shows decision fatigue, offer "use your recommended defaults and I'll review them in the PRD".

## After the interview

Add a short "The look, locked" section to the PRD (fonts, colors with hex values, shape rule, theme mode, shared brands), so the building agent has one place to read it.
