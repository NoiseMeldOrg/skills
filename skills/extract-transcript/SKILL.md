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
- **User provides a YouTube URL** — the transcript can be fetched automatically

## Quick Start

The simplest invocation is just a YouTube URL:

```
/extract-transcript https://www.youtube.com/watch?v=XXXXX
```

This will:
1. Fetch the transcript via the bundled `scripts/get_transcript.py`
2. Fetch the video title and channel via YouTube oembed API
3. Structure the content into a Markdown summary
4. File it in the appropriate folder and commit

## Process

### Step 0: Get the Transcript

If the user provides a YouTube URL instead of pasted text:

1. **Fetch the transcript** using the project's venv:
   ```bash
   .venv/bin/python {SKILL_DIR}/scripts/get_transcript.py "<youtube-url>"
   ```
2. **Fetch the video title and channel** via oembed:
   ```bash
   curl -s "https://www.youtube.com/oembed?url=<youtube-url>&format=json"
   ```
   Use the `title` and `author_name` fields in the Source block, and link to the video URL and channel URL (`author_url`).

If the user pastes the transcript directly, skip this step.

### Step 1: Identify Metadata

From the transcript and any context the user provides, determine:

- **Speaker** — name and credentials (MD, PhD, surgeon, etc.) if known
- **Source** — YouTube, podcast name, interview, etc.
- **Date** — if mentioned or provided by user
- **Topic** — one-line description of the subject
- **Key references cited** — any studies, guidelines, or papers mentioned by name
- **Format** — solo presentation, interview (if so, who is the host), panel, etc.

If anything is unclear, ask the user.

### Step 2: Read and Organize

Read through the entire transcript. Identify:

1. The core argument or message
2. Natural section breaks (topic shifts, new points)
3. Key claims with evidence cited
4. Practical advice or action items
5. Notable quotes worth preserving

### Step 3: Write the Document

Use this exact structure:

```markdown
# [Video/Episode Title]

**Speaker:** [Name, credentials]
**Source:** [YouTube / podcast name / etc.]
**Date:** [if known]
**Topic:** [one-line description]
**Key references cited:** [studies, guidelines, books mentioned — if any]
**Published paper:** [if the video presents or discusses a specific published study — include author, journal, year, DOI, and a relative-path link to the study MD if one exists locally]

---

## Summary

[2-4 sentences capturing the core argument and conclusion]

**Key takeaway:** [one sentence — the single thing someone should remember]

---

## [Section 1: descriptive heading]

[Content organized into clear prose, not raw transcript. Clean up false starts,
filler words, repetition. Preserve the speaker's voice and key quotes (use > blockquotes
for particularly strong or quotable statements). Use subheadings if a section is long.]

## [Section 2]

[etc.]

---

## Source

**Video/Episode:** "[full title]"
**Presenter/Guest:** [name, credentials, affiliation]
**Host:** [if interview format]
**Resources mentioned:** [links, books, tools referenced — if any]
```

If the user's project CLAUDE.md defines a personal context to evaluate transcripts against (a medical case, a research focus, a product decision), add a final section before the Source block that connects the speaker's claims to that context. Be specific — cite numbers, open questions, and note where claims are testable vs. speculative. Skip this section when no project context applies.

### Step 4: File It

Ask the user where to save it unless the project's CLAUDE.md or an existing folder convention makes it obvious. Match the filing pattern of neighboring documents if there is one. A reasonable default filename is:

`[Short Title] - [Speaker Name].md`

### Step 5: Cross-Reference Related Docs

If the speaker discusses a published paper:

1. **Check the project for an existing extraction of that paper.** If one exists, add the "Published paper" metadata field with a relative-path link to it.
2. **If not, offer to extract it** using `extract-study` so both live in the repo and link to each other.
3. **Add the reverse link** in the study MD — open it and add a "See also" line pointing back to the transcript. Bidirectional links keep the pair discoverable from either side.

Also cross-reference related reference docs, letters, or other transcripts when the content overlaps substantively.

### Step 6: Commit

Add and commit with a descriptive message.

## Writing Guidelines

- This is a summary, not a transcription. Reorganize for clarity. Combine redundant points. Cut filler.
- Preserve the speaker's actual arguments and reasoning, not just conclusions.
- Use `> blockquotes` for particularly strong or memorable direct quotes.
- If the speaker cites a study, include enough detail to find it (author, journal, year if mentioned).
- If you write a project-specific relevance section, be honest — if the speaker is speculating or the evidence is weak, say so. If the speaker is not credentialed in the field they're discussing, note that.

## What This Skill Is NOT

- Not for research papers (use `extract-study`)
- Not for books (use `extract-book`)
- Not for medical appointment transcripts (those are diarized dialogues, handled differently)
