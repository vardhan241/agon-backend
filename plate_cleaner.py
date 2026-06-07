
"""Indian number plate normalization and correction utilities.

The logic is intentionally deterministic and offline. It is tuned for the
standard private/commercial Indian format:

    [A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}

Examples: MH12AB1234, KA05MQ1234, DL01CAA1234.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

INDIAN_PLATE_REGEX = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$")

LETTER_CONFUSIONS = {
    "0": "O",
    "1": "I",
    "2": "Z",
    "4": "A",
    "5": "S",
    "6": "G",
    "8": "B",
}

DIGIT_CONFUSIONS = {
    "O": "0",
    "Q": "0",
    "D": "0",
    "I": "1",
    "L": "1",
    "T": "1",
    "Z": "2",
    "A": "4",
    "S": "5",
    "G": "0",
    "B": "8",
}

@dataclass(frozen=True)
class PlateCleanResult:
    raw_text: str
    normalized_text: str
    corrected_text: str
    is_valid: bool
    confidence_penalty: float
    notes: List[str]


def normalize_text(text: str) -> str:
    """Uppercase OCR text and remove all non-alphanumeric characters."""
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def _score_candidate(candidate: str) -> tuple[int, int]:
    match = INDIAN_PLATE_REGEX.search(candidate)
    if match:
        return (0, len(candidate) - len(match.group(0)))
    return (1, abs(10 - len(candidate)))


def _position_correct(text: str) -> tuple[str, list[str], float]:
    chars = list(text)
    notes: list[str] = []
    penalty = 0.0
    # Use the longest Indian format expectation: SS00LLL0000.
    pattern = ["L", "L", "D", "D", "L", "L", "D", "D", "D", "D"]
    for idx, char in enumerate(chars[: len(pattern)]):
        expected = pattern[idx]
        if expected == "L" and char in LETTER_CONFUSIONS:
            chars[idx] = LETTER_CONFUSIONS[char]
            notes.append(f"position {idx + 1}: {char}->{chars[idx]} as letter")
            penalty += 1.5
        elif expected == "D" and char in DIGIT_CONFUSIONS:
            chars[idx] = DIGIT_CONFUSIONS[char]
            notes.append(f"position {idx + 1}: {char}->{chars[idx]} as digit")
            penalty += 1.5
    return "".join(chars), notes, penalty


def clean_plate_text(raw_text: str) -> PlateCleanResult:
    normalized = normalize_text(raw_text)
    if not normalized:
        return PlateCleanResult(raw_text, "", "", False, 30.0, ["empty OCR result"])

    candidates = [normalized]
    corrected, notes, penalty = _position_correct(normalized)
    candidates.append(corrected)

    # OCR can include leading/trailing junk. Try every 9-11 char window.
    for width in (11, 10, 9):
        if len(corrected) >= width:
            for start in range(0, len(corrected) - width + 1):
                candidates.append(corrected[start : start + width])

    candidates = sorted(set(candidates), key=_score_candidate)
    for candidate in candidates:
        match = INDIAN_PLATE_REGEX.search(candidate)
        if match:
            final = match.group(0)
            final_notes = notes + (["regex extracted valid Indian plate"] if final != normalized else ["valid without extraction"])
            return PlateCleanResult(raw_text, normalized, final, True, penalty, final_notes)

    print("Corrected =", corrected)
    print("Regex match =", INDIAN_PLATE_REGEX.search(corrected))
    
    return PlateCleanResult(raw_text, normalized, corrected, False, min(35.0, penalty + 12.0), notes + ["regex validation failed"])
    print("Corrected:", corrected)

def is_valid_indian_plate(text: str) -> bool:
    return bool(INDIAN_PLATE_REGEX.fullmatch(normalize_text(text)))
