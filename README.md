# Web Scraper Summarizer

Minimal Python CLI utility that fetches a public web page, extracts the readable text, and produces a concise summary.

## Features

- Downloads HTML with robust error handling and User-Agent spoofing.
- Cleans the document and keeps the main textual content.
- Generates an extractive summary using a frequency-based ranking algorithm.
- Outputs both the page title and summary to the console or optionally to a file.

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

Run the scraper from the repository root:

```bash
python -m src.scraper --url https://example.com --sentences 4
```

Optional arguments:

- `--sentences`: Number of sentences in the summary (default 5).
- `--min-chars`: Minimum character count for a sentence to be considered (default 40).
- `--output`: Path to write the summary to disk instead of printing to stdout.

## Notes

- The summarizer is extractive; it selects representative sentences from the page.
- Some websites may block automated requests—use responsibly and respect robots.txt.
- For best results, target article-like pages with well-structured paragraphs.

