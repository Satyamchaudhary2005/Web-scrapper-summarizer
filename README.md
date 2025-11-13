# Web Scraper Summarizer

Python toolkit for fetching a public web page, extracting the readable text, and producing a concise extractive summary. It ships with both a command-line interface and a lightweight Flask web UI so anyone can generate summaries in the browser.

## Features

- Downloads HTML with robust error handling and User-Agent spoofing.
- Cleans the document and keeps the main textual content.
- Generates an extractive summary using a frequency-based ranking algorithm.
- Works via CLI or browser-based interface.

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

## CLI Usage

Run the scraper from the repository root:

```bash
python -m src.scraper --url https://example.com --sentences 4
```

Optional arguments:

- `--sentences`: Number of sentences in the summary (default 5).
- `--min-chars`: Minimum character count for a sentence to be considered (default 40).
- `--output`: Path to write the summary to disk instead of printing to stdout.

## Web App Usage

Start the Flask development server:

```bash
flask --app src.webapp run --reload
```

Then open http://127.0.0.1:5000/ in your browser, paste a URL, and click **Summarize**. The page returns the article title, a bulleted summary, and (optionally) the extracted text.

## Notes

- The summarizer is extractive; it selects representative sentences from the page.
- Some websites may block automated requests—use responsibly and respect robots.txt.
- For best results, target article-like pages with well-structured paragraphs.

