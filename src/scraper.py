from __future__ import annotations

import argparse
import logging
import re
from collections import Counter
from dataclasses import dataclass
from heapq import nlargest
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

STOP_WORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "could",
    "did",
    "do",
    "does",
    "doing",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "now",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
}


class ScraperError(RuntimeError):
    """Custom error type for scraper failures."""


@dataclass
class PageContent:
    title: str
    sentences: list[str]

    @property
    def text(self) -> str:
        return " ".join(self.sentences)


def fetch_html(url: str, timeout: int = 15) -> str:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise ScraperError(f"Network error while fetching '{url}': {exc}") from exc

    if not response.ok:
        raise ScraperError(
            f"Unexpected status code {response.status_code} while fetching '{url}'"
        )

    response.encoding = response.apparent_encoding or response.encoding
    return response.text


def extract_sentences(html: str) -> PageContent:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "header", "footer", "form"]):
        tag.decompose()

    title_tag = soup.find("title")
    title = title_tag.text.strip() if title_tag and title_tag.text else "Untitled page"

    paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
    if not paragraphs:
        raw_text = soup.get_text(separator=" ")
    else:
        raw_text = " ".join(paragraphs)

    cleaned = re.sub(r"\s+", " ", raw_text).strip()
    if not cleaned:
        raise ScraperError("Unable to extract textual content from the page.")

    sentences = split_sentences(cleaned)
    return PageContent(title=title, sentences=sentences)


def split_sentences(text: str) -> list[str]:
    sentence_endings = re.compile(r"(?<=[.!?])\s+")
    candidates = sentence_endings.split(text)
    normalized = [candidate.strip() for candidate in candidates if candidate.strip()]
    return normalized


def summarize_sentences(
    sentences: Iterable[str],
    *,
    max_sentences: int,
    min_chars: int,
) -> list[str]:
    filtered = [s for s in sentences if len(s) >= min_chars]
    if not filtered:
        raise ScraperError(
            "Not enough substantial sentences were found to build a summary."
        )

    word_freq = Counter()
    sentence_scores: dict[str, float] = {}

    for sentence in filtered:
        words = tokenize_sentence(sentence)
        if not words:
            continue

        unique_words = set(words)
        for word in unique_words:
            word_freq[word] += 1

    if not word_freq:
        raise ScraperError("Failed to compute word frequencies for summarization.")

    for sentence in filtered:
        words = tokenize_sentence(sentence)
        sentence_scores[sentence] = sum(word_freq[word] for word in words)

    top_sentences = nlargest(max_sentences, filtered, key=sentence_scores.get)
    top_sentences.sort(key=lambda s: sentences.index(s))
    return top_sentences


def tokenize_sentence(sentence: str) -> list[str]:
    words = re.findall(r"[a-zA-Z]+", sentence.lower())
    return [word for word in words if word not in STOP_WORDS]


def format_summary(page: PageContent, summary_sentences: list[str]) -> str:
    lines = [
        page.title,
        "",
        *(f"- {sentence}" for sentence in summary_sentences),
    ]
    return "\n".join(lines)


def save_summary(summary: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(summary, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a web page and summarize its textual content."
    )
    parser.add_argument("--url", required=True, help="URL of the page to summarize.")
    parser.add_argument(
        "--sentences",
        type=int,
        default=5,
        help="Number of sentences to include in the summary.",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=40,
        help="Minimum character length of sentences considered for the summary.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to save the summary instead of printing to stdout.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging for troubleshooting.",
    )
    return parser.parse_args(argv)


def configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def run(url: str, *, sentences: int, min_chars: int) -> tuple[PageContent, list[str]]:
    html = fetch_html(url)
    page = extract_sentences(html)
    summary = summarize_sentences(page.sentences, max_sentences=sentences, min_chars=min_chars)
    return page, summary


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    configure_logging(args.debug)

    logging.debug("Starting summarization for URL: %s", args.url)
    try:
        page, summary = run(args.url, sentences=args.sentences, min_chars=args.min_chars)
    except ScraperError as err:
        logging.error("%s", err)
        raise SystemExit(1) from err

    result = format_summary(page, summary)

    if args.output:
        save_summary(result, args.output)
        logging.info("Summary written to %s", args.output)
    else:
        print(result)


if __name__ == "__main__":
    main()

