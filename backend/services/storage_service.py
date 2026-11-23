
import re
from difflib import SequenceMatcher

from backend.database import SessionLocal
from backend.models.db_models import (
    Meeting,
    TranscriptLine,
    Draft
)


def normalize_text(text):
    """Normalize text for reliable evidence comparison."""
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_evidence_source_line(transcript, evidence):
    """
    Find the transcript line supporting AI-generated evidence.

    Checks:
    1. Exact normalized match.
    2. Evidence across up to 3 consecutive transcript lines.
    3. High token coverage for minor wording differences.

    Returns the starting transcript line number or None.
    """

    if not evidence or not evidence.strip():
        return None

    evidence_normalized = normalize_text(evidence)

    if not evidence_normalized:
        return None

    evidence_tokens = set(evidence_normalized.split())

    transcript_lines = []

    current_speaker = None

    for line_number, raw_line in enumerate(
        transcript.splitlines(), start=1
    ):
        line = raw_line.strip()

        if not line:
            continue

        if line.endswith(":") and len(line) < 100:
            current_speaker = line[:-1].strip()
            continue

        normalized = normalize_text(line)

        if normalized:
            transcript_lines.append({
                "line_number": line_number,
                "text": normalized
            })

    best_match = None
    best_score = 0

    # Check windows of 1, 2 and 3 consecutive transcript lines.
    for start in range(len(transcript_lines)):

        for window_size in range(1, 4):

            end = start + window_size

            if end > len(transcript_lines):
                break

            window = transcript_lines[start:end]

            # Only combine consecutive original transcript lines.
            line_numbers = [
                item["line_number"] for item in window
            ]

            if any(
                line_numbers[i + 1] - line_numbers[i] > 1
                for i in range(len(line_numbers) - 1)
            ):
                break

            combined_text = " ".join(
                item["text"] for item in window
            )

            # Exact normalized match.
            if evidence_normalized in combined_text:
                return window[0]["line_number"]

            source_tokens = set(combined_text.split())

            if not evidence_tokens:
                continue

            token_coverage = (
                len(evidence_tokens.intersection(source_tokens))
                / len(evidence_tokens)
            )

            similarity = SequenceMatcher(
                None,
                evidence_normalized,
                combined_text
            ).ratio()

            # Conservative verification to reduce false positives.
            if len(evidence_tokens) >= 4:
                verified = (
                    token_coverage >= 0.90
                    and similarity >= 0.65
                )
            else:
                verified = similarity >= 0.90

            score = (token_coverage + similarity) / 2

            if verified and score > best_score:
                best_score = score
                best_match = window[0]["line_number"]

    return best_match


def save_meeting(
    meeting_date,
    filename,
    transcript,
    analysis
):

    db = SessionLocal()

    try:

        meeting = Meeting(
            meeting_date=meeting_date,
            filename=filename,
            transcript=transcript,
            summary=analysis["summary"]
        )

        db.add(meeting)
        db.flush()

        # Save transcript lines.
        current_speaker = None

        for line_number, raw_line in enumerate(
            transcript.splitlines(), start=1
        ):

            line = raw_line.strip()

            if not line:
                continue

            if line.endswith(":") and len(line) < 100:
                current_speaker = line[:-1].strip()
                continue

            db.add(
                TranscriptLine(
                    meeting_id=meeting.id,
                    line_number=line_number,
                    speaker=current_speaker,
                    text=line
                )
            )

        # Save AI-generated drafts.
        categories = [
            ("action_item", analysis["action_items"]),
            ("decision", analysis["decisions"]),
            ("risk", analysis["risks"]),
            ("scope_change", analysis["scope_changes"])
        ]

        for draft_type, items in categories:

            for item in items:

                evidence = item.get("evidence", "")

                matching_line = find_evidence_source_line(
                    transcript,
                    evidence
                )

                db.add(
                    Draft(
                        meeting_id=meeting.id,
                        draft_type=draft_type,
                        description=item["description"],
                        owner=item.get("owner"),
                        due_date=item.get("due_date"),
                        evidence=evidence,
                        source_line_number=matching_line,
                        evidence_verified=matching_line is not None,
                        status="pending"
                    )
                )

        db.commit()

        return meeting.id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
