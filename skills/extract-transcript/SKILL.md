---
name: extract-transcript
description: >
  This skill should be used when the user asks to "extract a transcript", "summarize this video",
  "make a doc from this transcript", or provides a YouTube URL, podcast transcript, or timestamped
  spoken-word content. Also triggers when the user pastes a raw transcript, mentions "here's a video
  from Dr. [name]", or drops a YouTube link without explicitly asking for extraction.
---

# Extract Video/Podcast Transcript to Structured Markdown

Convert raw transcripts (YouTube, podcast, interview) into clean, structured Markdown summaries. Unlike study extraction, this is a reasoning task — the transcript is messy spoken-word content that needs to be understood, organized, and summarized, not just reformatted.

## When to Use

- User pastes a raw transcript with timestamps
- User says "here's a video from [speaker]" and provides text
- User wants to file a YouTube video summary
- User drops a transcript and asks for a doc/summary
- **User provides a YouTube URL** — the transcript and metadata can be fetched automatically

## Quick Start

The simplest invocation is just a YouTube URL:

```
/extract-transcript https://www.youtube.com/watch?v=XXXXX
```

This will:
1. Fetch transcript + metadata as a JSON bundle via `scripts/get_transcript.py`
2. Use chapter markers (when available) as section scaffolding
3. Structure the content into a Markdown summary
4. Write it to the directory this Claude Code session was started in
5. Commit it (if that directory is a repo where transcripts belong)

## Process

### Step 0: Fetch the Bundle

If the user provides a YouTube URL instead of pasted text, run:

```bash
python3 {SKILL_DIR}/scripts/get_transcript.py "<youtube-url>" -o /tmp/bundle.json
```

The JSON bundle contains: `title`, `channel`, `channel_url`, `description`, `duration_seconds`, `upload_date`, `chapters`, `transcript_plain`, `transcript_timestamped`, `metadata_source`.

**Requires `youtube-transcript-api`.** If the script fails with `ModuleNotFoundError`, install it: `pip install youtube-transcript-api`.

**Prefer `yt-dlp` when available** — it gives richer and more reliable metadata (especially chapters and full descriptions). Install with `pip install yt-dlp` or `brew install yt-dlp`. The fallback path (oembed + YouTube watch-page scrape) works without it but is brittle; any field it can't resolve is `null`.

**How to use each field:**

- `description` — read it carefully. This is the single most valuable piece for disambiguating product/tool names the transcript garbles, finding resource links the speaker referenced, and confirming credentials. When in doubt about a term from the transcript, check the description first.
- `chapters` — when present, use chapter titles as your section scaffolding (H2 headings). They're the creator's own outline, which is almost always cleaner than what you'd infer.
- `duration_seconds` + `upload_date` — include both in the metadata header. Readers need to know how fresh the advice is and whether it's worth watching.
- `transcript_timestamped` — use this to embed timestamp anchors on key quotes. Format: `https://www.youtube.com/watch?v=<id>&t=<seconds>s`. Do this for 3–8 notable quotes, not every quote — this is the feature that makes the doc useful as a navigation index back to the video.
- `transcript_plain` — the primary content to summarize.

If the user pastes the transcript directly, skip Step 0 and move to Step 1.

### Step 1: Identify Metadata

Most fields come straight from the bundle. You still need to infer:

- **Speaker credentials** — the bundle has `channel` (YouTube name) but not credentials. Check the description for "I'm a [role]" self-descriptions. If still unclear, say so explicitly in the doc ("no stated credentials").
- **Format** — solo presentation, interview, panel. Usually obvious from the transcript; ask if not.
- **Topic** — one-line description you write yourself.
- **Key references cited** — studies, guidelines, books, or products mentioned by name. Pull these from the transcript.
- **Transcription uncertainties** — proper nouns the transcript may have garbled. Names of products, people, or organizations you can't fully verify from the description or the transcript. Collect these as you read so you can surface them in a dedicated block (see template).

### Step 2: Read and Organize

Read through the entire transcript. If chapters are available, use them as your section boundaries. Otherwise identify:

1. The core argument or message
2. Natural section breaks (topic shifts, new points)
3. Key claims with evidence cited
4. Practical advice or action items
5. Notable quotes worth preserving

**Decide: tutorial or argument mode.** A tutorial ("here's how I built X," "step 1, step 2…") is best served by an up-front reproducible-steps block before the narrative. An argument-driven talk (a research summary, an opinion piece, an interview) is best served by the standard narrative template.

### Step 3: Write the Document

Use this exact structure. Fields marked `[optional]` are omitted when not applicable.

```markdown
# [Video/Episode Title]

**Speaker:** [Name, credentials if known]
**Source:** [YouTube / podcast name / etc.]
**Published:** [upload_date — YYYY-MM-DD]
**Runtime:** [HH:MM:SS or ~N minutes]
**Topic:** [one-line description]
**Format:** [solo tutorial, interview, panel, etc.]
**Key references cited:** [studies, guidelines, tools, books mentioned — if any]
**Published paper:** [optional — if the video presents a specific published study, include author/journal/year/DOI and a relative-path link to the study MD if one exists locally]

> **Transcription uncertainties:** [optional — a single line or short list of proper nouns, product names, or speaker claims Claude couldn't fully verify. Include these so the user can correct them in one pass. Omit the block entirely if everything resolved cleanly.]

---

## Summary

[2–4 sentences capturing the core argument and conclusion.]

**Key takeaway:** [one sentence — the single thing someone should remember]

---

## [For tutorials only — optional up-front block]

### Steps to reproduce

1. [Short imperative step with command/link if applicable]
2. [...]

[When the video is a how-to build, put the extracted reproducible steps up front. Link each step to its timestamp in the video with `[time](url?t=Ns)`. Narrative sections below can then focus on *why*, not *what*.]

---

## [Section 1: from chapter title if available, or your own heading]

[Content organized into clear prose, not raw transcript. Clean up false starts,
filler words, repetition. Preserve the speaker's voice and key quotes.]

> Use blockquotes for particularly strong or quotable statements. ([1:22](https://www.youtube.com/watch?v=VIDEO_ID&t=82s))

[Embed `?t=Ns` timestamp anchors on 3–8 notable quotes across the doc — not every quote. Enough that a reader can jump back into the video at the moments that matter, not so many that it becomes noise.]

## [Section 2]

[etc.]

---

## Source

**Video/Episode:** "[full title]"
**URL:** [video URL]
**Channel:** [channel name linked to channel URL]
**Presenter/Guest:** [name, credentials, affiliation]
**Host:** [if interview format]
**Sponsor:** [if disclosed in the video]
**Resources mentioned:** [links pulled from the description and transcript — books, tools, prior videos, referenced channels]
```

If the user's project CLAUDE.md or user-level memory defines a personal context to evaluate transcripts against (a medical case, a research focus, a product decision), add a "Personal relevance" section before the Source block that connects the speaker's claims to that context. Be specific — cite numbers, open questions, and note where claims are testable vs. speculative. Skip this section when no project context applies.

### Step 4: File It

**Default: write the file to the directory this Claude Code session was started in** — the primary working directory shown in your environment. This is the user's implicit "current workspace" and is almost always where they expect output to land.

**Guard against dumping notes into a code repo.** If the session started in a git repository that has no existing transcript-like docs (no `transcripts/` folder, no sibling `.md` files that look like prior transcripts), ask the user where to save before writing. It's much cheaper to ask once than to write into the wrong place and pollute a tracked repo.

**Filename default:** `[Short Title] - [Speaker Name].md`. Match an existing filename pattern in the target folder if one is obvious.

### Step 5: Cross-Reference Related Docs

If the speaker discusses a published paper:

1. **Check the project for an existing extraction of that paper.** If one exists, add the "Published paper" metadata field with a relative-path link to it.
2. **If not, offer to extract it** using `extract-study` so both live in the repo and link to each other.
3. **Add the reverse link** in the study MD — open it and add a "See also" line pointing back to the transcript. Bidirectional links keep the pair discoverable from either side.

Also cross-reference related reference docs, letters, or other transcripts when the content overlaps substantively.

### Step 6: Commit

If the file was written into a git repository where transcripts belong, add and commit with a descriptive message. If it was written to a non-git directory, skip this step.

## Writing Guidelines

- This is a summary, not a transcription. Reorganize for clarity. Combine redundant points. Cut filler.
- Preserve the speaker's actual arguments and reasoning, not just conclusions.
- Use `> blockquotes` for particularly strong or memorable direct quotes. Anchor 3–8 of them to their video timestamps.
- If the speaker cites a study, include enough detail to find it (author, journal, year if mentioned).
- If you write a personal-relevance section, be honest — if the speaker is speculating or the evidence is weak, say so. If the speaker is not credentialed in the field they're discussing, note that.
- **Surface transcription uncertainties at the top.** A named product or person you couldn't verify goes in the dedicated block, not buried in prose — the user fixes these in one pass that way.

## What This Skill Is NOT

- Not for research papers (use `extract-study`)
- Not for books (use `extract-book`)
- Not for medical appointment transcripts (those are diarized dialogues, handled differently)
