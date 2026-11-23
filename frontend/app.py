import streamlit as st
import requests
from datetime import date

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Project Manager",
    page_icon="🤖",
    layout="wide"
)


def api_get(endpoint):
    response = requests.get(
        f"{API_URL}{endpoint}",
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def api_post(endpoint, payload=None):
    response = requests.post(
        f"{API_URL}{endpoint}",
        json=payload or {},
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def api_put(endpoint, payload):
    response = requests.put(
        f"{API_URL}{endpoint}",
        json=payload,
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def show_error(error):
    if isinstance(error, requests.HTTPError):
        try:
            detail = error.response.json()
        except Exception:
            detail = error.response.text
        st.error(f"API Error: {detail}")
    else:
        st.error(f"Error: {error}")


st.title("🤖 AI Project Manager Agent")
st.caption("Meeting Intelligence | Human Approval | Jira Integration")

page = st.sidebar.radio(
    "Navigation",
    [
        "Meeting Analysis",
        "Approval Dashboard",
        "Jira Tasks"
    ]
)


if page == "Meeting Analysis":

    st.header("📄 Meeting Transcript Analysis")

    meeting_date = st.date_input(
        "Meeting Date",
        value=date.today()
    )

    uploaded_file = st.file_uploader(
        "Upload meeting transcript",
        type=["txt", "vtt"]
    )

    if st.button("Analyze Meeting", type="primary"):

        if uploaded_file is None:
            st.error("Please upload a transcript.")

        else:
            with st.spinner("Analyzing meeting using Groq..."):

                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "text/plain"
                        )
                    }

                    data = {
                        "meeting_date": meeting_date.isoformat()
                    }

                    response = requests.post(
                        f"{API_URL}/analyze-meeting",
                        files=files,
                        data=data,
                        timeout=180
                    )

                    response.raise_for_status()
                    result = response.json()

                    st.session_state["analysis"] = result["analysis"]

                    st.success(
                        f"Meeting analyzed successfully! "
                        f"Meeting ID: {result['meeting_id']}"
                    )

                except requests.RequestException as error:
                    show_error(error)

    if "analysis" in st.session_state:

        result = st.session_state["analysis"]

        st.divider()
        st.subheader("Meeting Summary")
        st.info(result["summary"])

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Action Items")

            for item in result["action_items"]:
                with st.expander(item["description"]):
                    st.write("Owner:", item.get("owner") or "Not assigned")
                    st.write("Due date:", item.get("due_date") or "Not specified")
                    st.caption(item["evidence"])

        with col2:
            st.subheader("Decisions")

            for item in result["decisions"]:
                st.write("•", item["description"])
                st.caption(item["evidence"])

        st.subheader("Risks")

        for item in result["risks"]:
            st.warning(item["description"])
            st.caption(item["evidence"])

        st.subheader("Scope Changes")

        for item in result["scope_changes"]:
            st.info(item["description"])
            st.caption(item["evidence"])


elif page == "Approval Dashboard":

    st.header("✅ PM Approval Dashboard")

    if st.button("Refresh Drafts"):
        st.rerun()

    try:
        drafts = api_get("/drafts/pending").get("drafts", [])

        if not drafts:
            st.info("No pending drafts.")

        else:
            meeting_ids = sorted(
                {d["meeting_id"] for d in drafts},
                reverse=True
            )

            selected_meeting = st.selectbox(
                "Select Meeting",
                ["All Meetings"] + meeting_ids
            )

            if selected_meeting != "All Meetings":
                drafts = [
                    d for d in drafts
                    if d["meeting_id"] == selected_meeting
                ]

            col1, col2, col3 = st.columns(3)

            col1.metric("Pending Drafts", len(drafts))

            col2.metric(
                "Verified",
                sum(bool(d["evidence_verified"]) for d in drafts)
            )

            col3.metric(
                "Unverified",
                sum(not d["evidence_verified"] for d in drafts)
            )

            categories = {
                "action_item": "Action Items",
                "decision": "Decisions",
                "risk": "Risks",
                "scope_change": "Scope Changes"
            }

            for category, title in categories.items():

                items = [
                    d for d in drafts
                    if d["draft_type"] == category
                ]

                if not items:
                    continue

                st.subheader(title)

                for draft in items:

                    draft_id = draft["id"]

                    with st.container(border=True):

                        st.markdown(
                            f"**Draft #{draft_id}** "
                            f"| Meeting #{draft['meeting_id']}"
                        )

                        if draft["evidence_verified"]:
                            st.success("Evidence verified")
                        else:
                            st.error("Evidence not verified")

                        with st.expander("Transcript evidence"):
                            st.write(draft.get("evidence") or "No evidence")
                            st.caption(
                                f"Source line: "
                                f"{draft.get('source_line_number') or 'N/A'}"
                            )

                        with st.form(f"draft_{draft_id}"):

                            description = st.text_area(
                                "Description",
                                value=draft["description"]
                            )

                            col1, col2 = st.columns(2)

                            with col1:
                                owner = st.text_input(
                                    "Owner",
                                    value=draft.get("owner") or ""
                                )

                            with col2:
                                due_date = st.text_input(
                                    "Due date (YYYY-MM-DD)",
                                    value=draft.get("due_date") or ""
                                )

                            comments = st.text_input("PM Comments")

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                save = st.form_submit_button("💾 Save")

                            with col2:
                                approve = st.form_submit_button(
                                    "✅ Approve",
                                    disabled=not draft["evidence_verified"]
                                )

                            with col3:
                                reject = st.form_submit_button("❌ Reject")

                            if save:
                                try:
                                    api_put(
                                        f"/drafts/{draft_id}",
                                        {
                                            "description": description.strip(),
                                            "owner": owner.strip() or None,
                                            "due_date": due_date.strip() or None
                                        }
                                    )
                                    st.success("Draft updated.")
                                    st.rerun()

                                except requests.RequestException as error:
                                    show_error(error)

                            elif approve:
                                try:
                                    result = api_post(
                                        f"/drafts/{draft_id}/approve",
                                        {"comments": comments or None}
                                    )

                                    jira = result.get("jira", {})

                                    if jira.get("status") == "created":
                                        st.success(
                                            f"Created Jira issue {jira['issue_key']}"
                                        )
                                        st.link_button(
                                            "Open Jira Issue",
                                            jira["issue_url"]
                                        )
                                    elif jira.get("status") == "failed":
                                        st.warning(
                                            "Approved, but Jira creation failed: "
                                            + jira.get("message", "Unknown error")
                                        )
                                    else:
                                        st.success("Draft approved.")

                                    st.rerun()

                                except requests.RequestException as error:
                                    show_error(error)

                            elif reject:
                                try:
                                    api_post(
                                        f"/drafts/{draft_id}/reject",
                                        {"comments": comments or None}
                                    )
                                    st.warning("Draft rejected.")
                                    st.rerun()

                                except requests.RequestException as error:
                                    show_error(error)

    except requests.RequestException as error:
        show_error(error)


elif page == "Jira Tasks":

    st.header("🚀 Jira Tasks")
    st.write("Approved action items synchronized to Jira.")

    if st.button("Refresh Jira Tasks"):
        st.rerun()

    try:
        drafts = api_get(
            "/drafts/jira-created"
        ).get("drafts", [])

        col1, col2 = st.columns(2)

        col1.metric("Jira Tasks Created", len(drafts))

        col2.metric(
            "Approved Drafts",
            sum(d["status"] == "approved" for d in drafts)
        )

        if not drafts:
            st.info("No Jira tasks created yet.")

        else:
            for draft in drafts:

                with st.container(border=True):

                    st.subheader(draft["jira_issue_key"])
                    st.write(draft["description"])

                    st.caption(
                        f"Draft #{draft['id']} | "
                        f"Meeting #{draft['meeting_id']} | "
                        f"Owner: {draft.get('owner') or 'Unassigned'}"
                    )

                    st.link_button(
                        "Open in Jira",
                        draft["jira_issue_url"]
                    )

                    st.caption(
                        f"Created: {draft.get('jira_created_at') or 'N/A'}"
                    )

    except requests.RequestException as error:
        show_error(error)


st.divider()
st.caption("AI Project Manager Agent | Groq + FastAPI + SQLite + Jira")