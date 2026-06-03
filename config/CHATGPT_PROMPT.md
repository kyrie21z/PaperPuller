# PaperPuller Configuration Generator

Copy this entire message and send it to your AI assistant (ChatGPT, Claude, etc.) that has memory of your research interests. The AI will ask you questions about your research area, then generate the configuration files you need.

---

I'm setting up PaperPuller (https://github.com/JoeLeelyf/customize-arxiv-daily), a tool that fetches recent arXiv papers and uses an LLM to score them based on my research interests. I need you to generate my personalized configuration files.

Please ask me questions to understand:
1. What research field(s) I'm in and what specific problems I work on
2. What kinds of papers would be high-priority must-reads for me
3. What kinds of papers are irrelevant and should be down-ranked
4. What arXiv categories are relevant (e.g., cs.CV, cs.AI, cs.LG)
5. What keywords should be used to search arXiv
6. How papers should be grouped in the daily report (3-8 groups)
7. Any extra evaluation fields I'd like the LLM to return (beyond score, tags, reason, tldr)

Then generate these two files:

### File 1: `config/interest.md`

Use this structure:

```markdown
# Research Interest Profile

<2-3 sentences describing my research area and what I'm looking for>

## Evaluation Criteria

<What makes a paper high-score (7-10) vs medium (4-6) vs low (1-3)>

## Groups

- Group Name A: <description of papers belonging here>
- Group Name B: <description of papers belonging here>
- ...

## Local Keywords (optional)

- TagName1: keyword1, keyword2, ...
- TagName2: keyword3, keyword4, ...

## Extra Fields (optional)

<Describe any additional fields the LLM should return in the `extra` JSON object>
```

### File 2: `config/paperpuller.yaml` (relevant sections)

```yaml
arxiv:
  categories:
    - cs.XX
    - cs.YY
  fetch_days: 1
  keyword_queries:
    - keyword phrase one
    - keyword phrase two

ranking:
  high_priority_threshold: 7
  possible_threshold: 4
  max_report_papers: 50
```

After generating the files, tell me to create `config/interest.md` with the first file's content, and update the relevant sections in my existing `config/paperpuller.yaml`.
