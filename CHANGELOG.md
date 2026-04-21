# Changelog

Version numbers follow the commit count on `main`: version `1.0.N` is the Nth commit. To find the exact code for any version:

```bash
git log --oneline main | head -N
```

## 1.0.9

- Add auto-versioning from git commit count (mirrors rapture-ios scheme)
- Add CHANGELOG.md
- Document update workflow for plugin marketplace and symlink users

## 1.0.8

- Expand clear-and-concise-humanization provenance (obra, WikiProject AI Cleanup, blader)

## 1.0.7

- Credit source skills: writing-clearly-and-concisely (joshuadavidthomas) and humanize-writing (jpeggdev)

## 1.0.6

- Add extract-webpage skill (trafilatura-based web page extraction)
- Update extraction-skills bundle to include extract-webpage

## 1.0.5

- Rewrite README: humanize prose, add skill invocation guidance

## 1.0.4

- Document installation methods and per-skill usage

## 1.0.3

- Allow individual skill installation alongside bundles

## 1.0.2

- Add marketplace.json, README, LICENSE, .gitignore

## 1.0.1

- Initial commit: 5 skills (extract-book, extract-study, extract-transcript, clear-and-concise-humanization, explain-code)
