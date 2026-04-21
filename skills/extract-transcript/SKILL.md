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
**Published paper:** [if the video presents or discusses a specific published study — include author, journal, year, DOI, and a relative-path link to the study MD if it's already in `archive/docs/studies/`]

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

## Relevance to Michael's Situation

[Connect the content to Michael's specific case: CAC 1,806, metabolic health scorecard (4/5),
pending CCTA May 19, family history (father CAD since 50s, MI at 80), statin decision,
pending labs (Lp(a), hsCRP, ApoB, fasting insulin), carnivore diet, Dr. Baker relationship.

Be specific — cite actual numbers, pending tests, or open questions from other documents.
Note where the speaker's claims are testable vs. speculative.

If the transcript isn't relevant to Michael's cardiovascular case, say so and note what
topic it does relate to.]

---

## Source

**Video/Episode:** "[full title]"
**Presenter/Guest:** [name, credentials, affiliation]
**Host:** [if interview format]
**Resources mentioned:** [links, books, tools referenced — if any]
```

### Step 4: File It

Save to `archive/docs/cardiovascular/videos/` (or the appropriate topic subdir's `videos/` folder) with the filename format:

`[Short Title] - [Speaker Name].md`

Examples:
- `Baby Aspirin for Primary Prevention - Dr Ken Berry.md`
- `5 Year Carnivore Shocking CAC Increase - Dr Shawn Baker.md`

Do not place transcripts at the `archive/docs/cardiovascular/` root — all video summaries live in the `videos/` subdir. Match existing neighbors.

### Step 5: Cross-Reference Related Docs

If the speaker discusses a published paper:

1. **Check if the paper is already in `archive/docs/studies/`.** If yes, add the "Published paper" metadata field with a relative-path link (e.g., `../../studies/Koutnik 2024 - Long-term Ketogenic Diet T1D Case Report.md` from a file in `cardiovascular/videos/`).
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
- The "Relevance to Michael's Situation" section should be honest — if the speaker is speculating or the evidence is weak, say so. If the speaker is not a physician, note that.
- Do not use bold or em dashes in the Relevance section if the document will be shared with family (per user preference for personal-voice documents). For clinical reference docs that stay in the repo, standard markdown formatting is fine.

## What This Skill Is NOT

- Not for research papers (use `extract-study`)
- Not for books (use `extract-book`)
- Not for medical appointment transcripts (those are diarized dialogues, handled differently)
