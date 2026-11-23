from backend.agents.meeting_agent import analyze_meeting


def process_meeting(transcript, meeting_date):

    if not transcript.strip():
        raise ValueError("Transcript cannot be empty")

    result = analyze_meeting(
        transcript=transcript,
        meeting_date=meeting_date
    )

    return result