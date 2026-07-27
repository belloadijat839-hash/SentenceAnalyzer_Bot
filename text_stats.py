from __future__ import annotations

import re
from dataclasses import dataclass

# Common abbreviations that shouldn't be treated as sentence-enders.
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc",
    "e.g", "i.e", "approx", "apt", "no", "inc", "ltd", "co", "u.s", "u.k",
}

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
_WORD_RE = re.compile(r"[A-Za-z']+")
_VOWEL_RE = re.compile(r"[aeiouy]+")


@dataclass
class TextStats:
    sentence_count: int
    word_count: int
    char_count: int
    char_count_no_spaces: int
    avg_words_per_sentence: float
    avg_word_length: float
    syllable_count: int
    reading_time_seconds: int
    flesch_reading_ease: float
    reading_level: str


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []

    # Protect known abbreviations from being treated as sentence boundaries
    # by temporarily replacing their trailing period.
    protected = text
    for abbr in _ABBREVIATIONS:
        pattern = re.compile(rf"\b{re.escape(abbr)}\.", re.IGNORECASE)
        protected = pattern.sub(lambda m: m.group(0).replace(".", "\u0000"), protected)

    raw_sentences = _SENTENCE_SPLIT_RE.split(protected)

    sentences = []
    for s in raw_sentences:
        s = s.replace("\u0000", ".").strip()
        if s:
            sentences.append(s)

    # Fallback: if no terminal punctuation was found at all, treat the
    # whole text as a single sentence rather than reporting zero.
    if not sentences and text:
        sentences = [text]

    return sentences


def count_syllables(word: str) -> int:
    word = word.lower()
    matches = _VOWEL_RE.findall(word)
    count = len(matches)
    if word.endswith("e") and not word.endswith("le") and count > 1:
        count -= 1
    return max(count, 1)


def _reading_level(score: float) -> str:
    if score >= 90:
        return "Very easy (5th grade)"
    if score >= 80:
        return "Easy (6th grade)"
    if score >= 70:
        return "Fairly easy (7th grade)"
    if score >= 60:
        return "Standard (8th-9th grade)"
    if score >= 50:
        return "Fairly difficult (10th-12th grade)"
    if score >= 30:
        return "Difficult (college level)"
    return "Very difficult (college graduate)"


def analyze(text: str) -> TextStats:
    sentences = split_sentences(text)
    words = _WORD_RE.findall(text)

    sentence_count = max(len(sentences), 1)
    word_count = len(words)
    char_count = len(text)
    char_count_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))

    syllable_count = sum(count_syllables(w) for w in words) if words else 0

    avg_words_per_sentence = word_count / sentence_count if sentence_count else 0.0
    avg_word_length = (sum(len(w) for w in words) / word_count) if word_count else 0.0

    # Average adult reading speed ~200 words per minute.
    reading_time_seconds = round((word_count / 200) * 60) if word_count else 0

    if word_count and sentence_count:
        flesch = (
            206.835
            - 1.015 * (word_count / sentence_count)
            - 84.6 * (syllable_count / word_count)
        )
    else:
        flesch = 0.0
    flesch = round(max(min(flesch, 121.22), -100.0), 1)

    return TextStats(
        sentence_count=len(sentences) if sentences else 0,
        word_count=word_count,
        char_count=char_count,
        char_count_no_spaces=char_count_no_spaces,
        avg_words_per_sentence=round(avg_words_per_sentence, 1),
        avg_word_length=round(avg_word_length, 1),
        syllable_count=syllable_count,
        reading_time_seconds=reading_time_seconds,
        flesch_reading_ease=flesch,
        reading_level=_reading_level(flesch) if word_count else "N/A",
    )


def format_stats(stats: TextStats) -> str:
    minutes, seconds = divmod(stats.reading_time_seconds, 60)
    reading_time_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"

    return (
        "*Text Analysis*\n\n"
        f"Sentences: *{stats.sentence_count}*\n"
        f"Words: *{stats.word_count}*\n"
        f"Characters: *{stats.char_count}* ({stats.char_count_no_spaces} without spaces)\n"
        f"Syllables: *{stats.syllable_count}*\n\n"
        f"Avg words/sentence: *{stats.avg_words_per_sentence}*\n"
        f"Avg word length: *{stats.avg_word_length}* chars\n"
        f"Estimated reading time: *{reading_time_str}*\n\n"
        f"Flesch Reading Ease: *{stats.flesch_reading_ease}*\n"
        f"Reading level: _{stats.reading_level}_"
    )
