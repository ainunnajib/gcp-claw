---
name: text-stats
description: Analyze text documents for word count, character count, reading time, and most frequent words. Use when the user asks about document statistics or text analysis.
metadata:
  author: gcpclaw
  version: "1.0"
---

# Text Statistics Skill

When the user asks for text statistics or document analysis, use the `read_file` tool
to load the file, then compute the following metrics:

1. **Word count**: Split on whitespace
2. **Character count**: Total characters including/excluding spaces
3. **Line count**: Number of lines
4. **Reading time**: Estimate at 200 words per minute
5. **Top 10 words**: Most frequently used words (excluding common stop words)

## Stop words to exclude
a, an, the, is, it, of, in, to, and, or, for, on, at, by, with, as, this, that, from, be, are, was, were, been, has, have, had, do, does, did, will, would, could, should, may, might, can, not, no, but, if, so, all, its, my, your, his, her, our, their, i, we, you, he, she, they, me, us, him, them

## Output format
Present results in a clean markdown table.
