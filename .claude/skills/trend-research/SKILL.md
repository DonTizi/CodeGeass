---
name: trend-research
description: Deep social media trend research with Google Sheets export. Manual command only.
disable-model-invocation: true
allowed-tools: WebSearch, WebFetch, mcp__google-sheets__get_sheet_data, mcp__google-sheets__update_cells
argument-hint: [topic]
---

# /trend-research

Deep research on a topic across Reddit, X/Twitter, and Hacker News. Generates analyst report, calculates sentiment score, and writes everything to Google Sheets with ready-to-publish social content.

---

## MANDATORY CONSTRAINTS - DO NOT IGNORE

```
SOURCES: ONLY Reddit, X/Twitter, Hacker News
DATE: ONLY TODAY's content (current date)

NO blogs, Medium, news sites, YouTube, or any other source
NO content from yesterday or earlier

If a result is not from Reddit/X/HN -> REJECT
If a result is not from today -> REJECT
```

---

## Configuration

**Google Sheet ID:** `19pS7cHrX_PfEchBQVw6aC8TZC2uGHN3UmOmcq2J6uw0`
**Sheet:** `Daily AI Review`

## Sheet Columns

| Col | Content |
|-----|---------|
| A | Date |
| B | Topic |
| C | Sentiment Score (1-10) |
| D | Report |
| E | Forecasting |
| F | Sources |
| G | X Tweets - Sam Altman Style (5) |
| H | X Tweets - Boris Cherny Style (5) |
| I | LinkedIn Posts (5 mixed styles) |

## CRITICAL RULES - READ CAREFULLY

### ALLOWED SOURCES - ONLY THESE 3:
1. **Reddit** (reddit.com)
2. **X/Twitter** (x.com, twitter.com)
3. **Hacker News** (news.ycombinator.com, hn.algolia.com)

**ANY OTHER SOURCE = REJECT IT. Do NOT include Medium, blogs, news sites, YouTube, or anything else.**

### DATE FILTER - TODAY ONLY

**MANDATORY**: Every single result MUST be from TODAY's date.

Before starting:
1. Get today's date: Use format YYYY-MM-DD (example: 2026-01-28)
2. Calculate today's Unix timestamp at 00:00:00 UTC

**VALIDATION RULE**: Before including ANY result, verify:
- Is it from Reddit, X, or Hacker News? NO -> REJECT
- Is it from today's date? NO -> REJECT

If you cannot verify the date, REJECT the result.

---

## Workflow

### Step 1: Data Collection (TODAY ONLY - 3 SOURCES ONLY)

**First**: Determine today's date in YYYY-MM-DD format.

**Second**: Run ONLY these 4 searches (nothing else):

**1. Reddit (ONLY reddit.com):**
```
WebSearch: site:reddit.com "$ARGUMENTS" after:YYYY-MM-DD
```

**2. X/Twitter (ONLY x.com and twitter.com):**
```
WebSearch: site:x.com "$ARGUMENTS" after:YYYY-MM-DD
```
```
WebSearch: site:twitter.com "$ARGUMENTS" after:YYYY-MM-DD
```

**3. Hacker News (API with timestamp filter):**
```
WebFetch: https://hn.algolia.com/api/v1/search_by_date?query=$ARGUMENTS&tags=(story,comment)&numericFilters=created_at_i>UNIX_TIMESTAMP&hitsPerPage=50
```

Replace `UNIX_TIMESTAMP` with today's date at 00:00:00 UTC converted to Unix timestamp.

**Example for January 28, 2026:**
- Date: 2026-01-28
- Unix timestamp: 1769472000
- Full URL: `https://hn.algolia.com/api/v1/search_by_date?query=claude&numericFilters=created_at_i>1769472000&hitsPerPage=50`

**DO NOT run any other searches. NO "general articles". NO other sites.**

### Step 1.5: VALIDATION CHECKPOINT

After collecting results, go through EACH result and ask:
1. Is the domain reddit.com, x.com, twitter.com, or news.ycombinator.com?
   - NO -> DELETE from results
2. Is the date today (YYYY-MM-DD)?
   - NO -> DELETE from results
   - CANNOT VERIFY -> DELETE from results

**If you end up with 0 results after validation, report "No discussions found today on Reddit, X, or Hacker News for this topic." and STOP.**

### Step 2: Deep Extraction (VALIDATED RESULTS ONLY)

**ONLY extract from results that passed Step 1.5 validation.**

For each validated result (max 10-15), use WebFetch to extract:
- Full discussion content
- Comments and replies
- Engagement metrics:
  - Reddit: upvotes, comment count
  - X/Twitter: likes, retweets, replies
  - Hacker News: points, comment count
- Exact user quotes with usernames

**Source URL requirements:**
- Reddit: Must contain `reddit.com/r/`
- X: Must contain `x.com/` or `twitter.com/`
- HN: Must contain `news.ycombinator.com/item`

**If WebFetch fails or returns old content, SKIP that result.**

### Step 3: Sentiment Score Calculation (1-10)

**Scoring methodology:**

| Score | Meaning | Criteria |
|-------|---------|----------|
| 1-2 | Very negative | 80%+ negative mentions, severe criticism |
| 3-4 | Negative | 60-80% negative, frequent frustrations |
| 5 | Neutral | Balanced, no dominant sentiment |
| 6-7 | Positive | 60-80% positive, general satisfaction |
| 8-9 | Very positive | 80%+ positive, enthusiasm |
| 10 | Exceptional | 90%+ positive, viral enthusiasm |

**Formula:**
```
Score = 5 + ((%Positive - %Negative) / 20)
```

### Step 4: Report Writing

Write like a real equity/tech analyst. No bullet points. No emojis. Fluid prose.

**Report structure (plain text, no markdown):**

```
[EXECUTIVE SUMMARY]
2-3 punchy sentences on overall sentiment and main opportunity.

[SENTIMENT ANALYSIS]
Detailed description of what people really think. Quote real users with exact words. Explain nuances - not just "positive" or "negative" but WHY.

[FRICTION POINTS]
Concrete frustrations. What doesn't work? What do people want that doesn't exist? Specific examples with workarounds they use.

[WHAT WORKS]
What people love. Not generalities - specific features, use cases, "aha moments" mentioned.

[OPPORTUNITIES IDENTIFIED]
Quick services/products to build based on unmet needs. Include: problem solved, target, estimated complexity, traffic potential.
```

### Step 5: Forecasting (Separate Column)

Write predictions in a dedicated column:

```
[WILL WORK - 3-6 months]
- Prediction 1: Reason based on data
- Prediction 2: Reason based on data

[WILL FAIL - 3-6 months]
- Prediction 1: Reason based on data
- Prediction 2: Reason based on data

[WATCH CLOSELY]
- Trend 1: Why to monitor
- Trend 2: Why to monitor
```

### Step 6: Social Content Generation

---

## PSYCHOLOGY OF VIRAL CONTENT (Research-Backed)

Before writing any content, apply these scientifically-proven principles:

### Attention Science
- **8.25 seconds** - Average attention span (2025)
- **1.5 seconds** - Decision window to stop scrolling
- **30 minutes** - Critical engagement window after posting

### Algorithm Weights (Twitter Open Source)
```
Score = Likes x 1 + Retweets x 20 + Replies x 13.5 +
        Profile Clicks x 12 + Bookmarks x 10
```
**Key insight**: Retweets are 20x more valuable than likes. Write for shareability.

### Emotions That Perform (by amplification)
1. **Curiosity** - Information gap that demands resolution
2. **Surprise** - Pattern interrupt, unexpected insight
3. **Recognition** - "I've experienced this exact thing"
4. **Aspiration** - Future state they want to achieve

### Hook Types That Work
| Type | Example | Psychology |
|------|---------|------------|
| Bold declaration | "90% of productivity advice is wrong" | Challenge -> curiosity |
| Specific number | "47 seconds changed my entire workflow" | Specificity = credibility |
| Paradox | "The best founders spend less time working" | Cognitive dissonance |
| Vulnerability | "I almost quit last month. Here's why I didn't." | Emotional connection |
| Question | "What if everything you know about X is wrong?" | Open loop |

### Structure Rules
- **71-100 chars** = Optimal engagement
- **First person ("I")** = +23% engagement vs third person
- **Line breaks** = Better dwell time
- **No hashtags** or max 1-2 = Avoid spam signals

---

## PERSONA 1: SAM ALTMAN (@sama)

**Voice**: Visionary tech philosopher. States observations as universal truths.

### Psychological Profile

**Personality**: INTJ + Enneagram Type 4
- Independent, introspective, action-oriented
- Creates meaning through unprecedented work
- Takes no equity at OpenAI ($76K salary) - significance over wealth

**Core Beliefs**:
- "Self-belief bordering on delusion" is necessary for success
- "You can bend the world to your will. Most people don't even try."
- Speed of execution > perfect planning
- Working smart AND hard = 99th percentile

**What He Loves**:
- Founders who never give up
- Clear, concise communication
- Long-term thinking as competitive advantage
- Creating what never existed before

**What Frustrates Him**:
- Critics who question without building
- Pessimistic people (actively avoids them)
- Slow execution and hesitation
- Conventional thinking and safe choices

### Writing Style

**Patterns**:
- Short declarations (15-25 words)
- Single clauses, often fragments
- Observations stated as facts
- Minimal punctuation (periods only)
- NO EMOJIS EVER
- Lowercase, casual

**Rhetorical Devices**:
- Extremes: "Hire for slope, not Y-intercept"
- Paradoxes: Inverts conventional wisdom
- Patterns: "The number one predictor of..."
- Comparisons: "Most people focus on X. The best focus on Y."

**Tone**:
- Wry, occasionally provocative
- Never defensive
- Understated confidence
- Occasional dark humor

**Example Tweets**:
- "the number one predictor of success for a young startup: rate of iteration."
- "it's common to have vision; it's rare to have plans."
- "having the self-belief that you will be able to figure things out as you go along is critical to success."
- "hiring: values first, aptitude second, specific skills third."

**DO NOT**:
- Use emojis or exclamation marks
- Start with "I think" or "In my opinion"
- Be motivational/inspirational
- Use hashtags
- Sound defensive or uncertain
- Use corporate speak

---

## PERSONA 2: BORIS CHERNY (@bcherny)

**Voice**: Builder sharing learnings. Practical, pedagogical, humble.

### Psychological Profile

**Background**: Creator of Claude Code, author of "Programming TypeScript", former Facebook engineer, SF TypeScript Meetup organizer.

**Personality**: Pragmatic builder + teacher
- Shows work transparently
- Admits limitations openly
- Invites experimentation over prescribing
- Technical depth with accessibility

**Core Beliefs**:
- "Works great out of the box" - simplicity first
- Feedback loops are essential for quality
- Share your setup, let others adapt
- Build tools that work, then explain how

**What He Values**:
- Practical over theoretical
- Transparency about process
- Community and sharing
- Iteration and verification

### Writing Style

**Patterns**:
- "I use..." structure for practices
- "The most important thing..." for priorities
- "This saves me from..." for benefits
- Numbered lists (1-13) for clarity
- Technical terms in context, not jargon

**Tone**:
- Collaborative, not authoritative
- Honest about trade-offs
- Inviting experimentation
- Practical and grounded

**Thread Structure**:
- Opens with personal context
- Numbered tips/practices
- Specific tools and configs mentioned
- Closes with encouragement to adapt

**Example Tweets**:
- "I'm Boris and I created Claude Code. Lots of people have asked how I use Claude Code, so I wanted to show off my setup a bit."
- "My setup might be surprisingly vanilla! Claude Code works great out of the box, so I personally don't customize it much."
- "Probably the most important thing to get great results out of Claude Code -- give Claude a way to verify its work."
- "I use Opus 4.5 with thinking on for everything. The quality difference is worth it."

**Signature Phrases**:
- "works great out of the box"
- "the most important thing..."
- "this saves me from..."
- "I personally..."
- "give [tool] a way to verify its work"

**DO NOT**:
- Be preachy or authoritative
- Claim universal truths
- Hide limitations
- Use corporate marketing speak
- Oversell or hype

---

## TWEET GENERATION

Generate **5 tweets per persona** (10 total):

### Sam Altman Style (5 tweets)

Apply these formulas:

1. **Pattern Tweet** - Observation stated as universal truth
   - Formula: "[Topic]: [observation about what works/doesn't work]."
   - Example: "the best engineers i know spend 80% of their time thinking and 20% coding."

2. **Contrarian Tweet** - Invert conventional wisdom
   - Formula: "most people [common belief]. [inverted truth]."
   - Example: "most people optimize for not failing. the best optimize for magnitude of success."

3. **Paradox Tweet** - Point out an irony
   - Formula: "[seemingly contradictory observation]."
   - Example: "the fastest way to move slow is to try to move fast without thinking."

4. **Prediction Tweet** - State future as fact
   - Formula: "[what will happen] in [timeframe]."
   - Example: "most software will be written by AI within 3 years. the question is what humans will do instead."

5. **Hiring/Execution Tweet** - Specific actionable insight
   - Formula: "[domain]: [prioritized list or key insight]."
   - Example: "execution speed is the most reliable signal of founder quality."

### Boris Cherny Style (5 tweets)

Apply these formulas:

1. **Setup/Process Tweet** - Share how you do something
   - Formula: "I [practice]. [why it helps]."
   - Example: "I run 5 Claude instances in parallel. Most of my work is now reviewing and steering, not writing."

2. **Most Important Thing Tweet** - Highlight key insight
   - Formula: "The most important thing for [goal]: [specific practice]."
   - Example: "The most important thing for AI code quality: give it a way to verify its own work."

3. **Tool/Workflow Tweet** - Specific recommendation
   - Formula: "I use [tool/setting] for [purpose]. [benefit]."
   - Example: "I use Opus with extended thinking for everything. The quality difference is worth the extra tokens."

4. **Saves Me From Tweet** - Problem -> solution
   - Formula: "[Practice] saves me from [problem]."
   - Example: "CLAUDE.md saves me from re-explaining context every session."

5. **Works Great Tweet** - Encourage simplicity
   - Formula: "[Tool/approach] works great out of the box. [what most people overcomplicate]."
   - Example: "Claude Code works great out of the box. Most people overcustomize before they understand the defaults."

**Format for all tweets:**
```
---
[PERSONA] - [TYPE]
[Tweet content - max 280 chars]
---
```

---

## LINKEDIN POST GENERATION

Generate **5 LinkedIn posts** (mix of both personas):

### Post Types

1. **Pattern Post** (Sam style) - Industry observation
   - 2-3 short paragraphs
   - Observation -> implication -> what to do about it
   - No emojis, professional tone

2. **Process Post** (Boris style) - How I do X
   - Numbered list format
   - Specific tools/practices
   - "Adapt to your needs" closing

3. **Contrarian Post** (Sam style) - Challenge accepted wisdom
   - Bold opening statement
   - Evidence/reasoning
   - Reframe the conventional view

4. **Learnings Post** (Boris style) - What I learned from X
   - Personal context
   - Specific lessons (numbered)
   - Invitation to share their experience

5. **Prediction Post** (Sam style) - What's coming
   - State prediction as fact
   - Why it's inevitable
   - What it means for readers

**Format:**
```
---
[POST #X - TYPE - PERSONA STYLE]
[Title/Hook line]

[Post content - 100-200 words, no emojis]
---
```

### Step 7: Write to Google Sheets

1. Get last used row in sheet
2. Write to next row:

```
A: Today's date (DD/MM/YYYY)
B: Topic searched ($ARGUMENTS)
C: Sentiment score (1-10)
D: Full report
E: Forecasting section
F: All source URLs (separated by line breaks)
G: 5 Sam Altman style tweets (separated by "---")
H: 5 Boris Cherny style tweets (separated by "---")
I: 5 LinkedIn posts mixed styles (separated by "---")
```

## Style Rules

- ALL TEXT IN ENGLISH
- NO EMOJIS ANYWHERE
- Professional analyst tone
- Quote real users with attribution
- Cite specific engagement numbers
- Be concrete, not abstract
- State facts, not opinions

## SOURCE VALIDATION RULES (MANDATORY)

**BEFORE writing report, verify ALL sources in column F:**

1. **Domain check** - Every URL must be one of:
   - `reddit.com/r/...`
   - `x.com/...` or `twitter.com/...`
   - `news.ycombinator.com/item?id=...`

2. **Date check** - Every source must be from TODAY
   - If you cannot confirm the date, DO NOT include it

3. **NO EXCEPTIONS** - If a source fails either check:
   - Remove it from sources
   - Remove any quotes from that source in the report

**If after validation you have < 3 valid sources:**
- Report: "Insufficient data from Reddit/X/HN today for meaningful analysis"
- Set sentiment score to 5 (neutral/insufficient data)
- Skip forecasting

## Example Output

For `/trend-research Claude Code`:

| Column | Example |
|--------|---------|
| Date | 27/01/2026 |
| Topic | Claude Code |
| Score | 7 |
| Report | "Claude Code dominates developer mindshare with 65-70% positive sentiment..." |
| Forecasting | "WILL WORK: Tool ecosystem explosion..." |
| Sources | https://x.com/... |
| Sam Tweets | "most developers compare Claude Code to Cursor. they are solving different problems. one is a scalpel, the other is a bulldozer." |
| Boris Tweets | "I run 5 Claude Code instances in parallel. The most important thing: give Claude a way to verify its work. This saves me from reviewing broken code." |
| LinkedIn | "The number one complaint about Claude Code is not cost. It is memory. Every session starts from zero..." |

## Quick Reference: Writing Formulas

### Sam Altman Hooks
- "[domain]: [prioritized insight]."
- "most people [X]. the best [Y]."
- "the number one predictor of [outcome]: [factor]."

### Boris Cherny Hooks
- "I [practice]. [why it helps]."
- "The most important thing for [goal]: [practice]."
- "[Tool] works great out of the box."

### Psychological Triggers to Apply
1. **Curiosity gap** - Reveal partial info, not all
2. **Specificity** - "47 seconds" > "a short time"
3. **Recognition** - Make reader think "that's exactly my experience"
4. **Shareability** - Would someone retweet this to look smart?
