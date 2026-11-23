from backend.agents.meeting_agent import analyze_meeting

with open(
    "sample_data/meeting.txt",
    "r",
    encoding="utf-8"
) as file:

    transcript = file.read()


result = analyze_meeting(
    transcript=transcript,
    meeting_date="2026-11-23"
)

print("\n========== MEETING SUMMARY ==========")
print(result["summary"])

print("\n========== ACTION ITEMS ==========")

for item in result["action_items"]:
    print(item)

print("\n========== DECISIONS ==========")

for decision in result["decisions"]:
    print(decision)

print("\n========== RISKS ==========")

for risk in result["risks"]:
    print(risk)

print("\n========== SCOPE CHANGES ==========")

for change in result["scope_changes"]:
    print(change)