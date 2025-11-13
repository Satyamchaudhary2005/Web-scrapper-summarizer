from __future__ import annotations

from flask import Flask, render_template, request

from .scraper import ScraperError, run


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            result=None,
            error=None,
            form_defaults={"sentences": 5, "min_chars": 40},
        )

    @app.post("/")
    def summarize():
        url = request.form.get("url", "").strip()
        sentences = request.form.get("sentences", "5").strip()
        min_chars = request.form.get("min_chars", "40").strip()

        error = None
        result = None

        try:
            sentences_count = max(1, int(sentences))
            min_chars_count = max(10, int(min_chars))
        except ValueError:
            error = "Sentences and minimum characters must be numeric values."
            sentences_count = 5
            min_chars_count = 40
        else:
            if not url:
                error = "Please enter a valid URL."
            else:
                try:
                    page, summary = run(
                        url,
                        sentences=sentences_count,
                        min_chars=min_chars_count,
                    )
                    result = {
                        "title": page.title,
                        "url": url,
                        "summary": summary,
                        "full_text": page.text,
                    }
                except ScraperError as exc:
                    error = str(exc)

        return render_template(
            "index.html",
            result=result,
            error=error,
            form_defaults={
                "url": url,
                "sentences": sentences,
                "min_chars": min_chars,
            },
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

