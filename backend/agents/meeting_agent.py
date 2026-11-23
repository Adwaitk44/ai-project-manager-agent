
import json
from groq import Groq

from backend.config import settings
from backend.models.schemas import MeetingAnalysis


client = Groq(
    api_key=settings.GROQ_API_KEY
)


def analyze_meeting(transcript: str, meeting_date: str):

    prompt = f"""
You are an AI Project Manager Agent.

Meeting date: {meeting_date}

Analyze this meeting transcript.

Extract the following:

1. Meeting summary
2. Decisions
3. Action items
4. Risks and issues
5. Possible scope changes

IMPORTANT RULES:

- Never invent information.
- Never invent an owner.
- Never invent a deadline.
- Missing owners must be null.
- Missing deadlines must be null.
- Convert relative dates using the meeting date.
- If a date is ambiguous, return null.
- Every extracted item must have exact
  supporting transcript evidence.
- Distinguish decisions from suggestions.
- Scope changes must have status proposed.
- Do not create duplicate action items.
- Ignore irrelevant conversation.

Return valid JSON in this structure:

{{
    "summary": "Meeting summary",

    "decisions": [
        {{
            "description": "Decision",
            "evidence": "Exact transcript quote"
        }}
    ],

    "action_items": [
        {{
            "description": "Task description",
            "owner": null,
            "due_date": null,
            "evidence": "Exact transcript quote",
            "source_speaker": null
        }}
    ],

    "risks": [
        {{
            "description": "Risk description",
            "risk_type": "issue",
            "evidence": "Exact transcript quote"
        }}
    ],

    "scope_changes": [
        {{
            "description": "Requested change",
            "status": "proposed",
            "evidence": "Exact transcript quote"
        }}
    ]
}}

TRANSCRIPT:

{transcript}
"""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,

        messages=[
            {
                "role": "system",
                "content": "You extract project information accurately. Return JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.1,

        response_format={
            "type": "json_object"
        }
    )

    result = response.choices[0].message.content

    parsed_result = json.loads(result)

    validated_result = MeetingAnalysis.model_validate(
        parsed_result
    )

    return validated_result.model_dump()
