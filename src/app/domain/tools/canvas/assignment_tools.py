"""Assignment-specific Canvas tools.

Uses the Canvas API ``bucket`` parameter for server-side filtering instead of
downloading all assignments and filtering locally.

Canvas API bucket values:
  past | overdue | undated | ungraded | unsubmitted | upcoming | future
"""

from typing import Optional

from langchain.tools import tool

from .base import CanvasToolsHelper
from .formatters import format_assignments


def create_assignment_tools(helper: CanvasToolsHelper):
    """Create assignment-specific tools."""

    @tool("get_overdue_assignments")
    def get_overdue_assignments(course_identifier: Optional[str] = None) -> str:
        """Get assignments whose due date has passed and that have NOT been
        submitted.  Canvas marks these as "overdue".

        Use when the user asks:
        - "What assignments am I late on?"
        - "Do I have any overdue work?"
        - "What did I miss?"
        - "Am I missing any assignments?"

        Args:
            course_identifier: Optional course name, code, or ID.
        """
        course_id, course_name = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(
            course_id, include=["submission"], bucket="overdue"
        )
        title = f"{course_name} - Overdue" if course_id else "All Courses - Overdue"
        return (
            format_assignments(assignments, title)
            if assignments
            else "No overdue assignments! 🎉"
        )

    @tool("get_unsubmitted_assignments")
    def get_unsubmitted_assignments(course_identifier: Optional[str] = None) -> str:
        """Get assignments that the student has NOT yet submitted, regardless of
        whether they are overdue or still upcoming.

        Use when the user asks:
        - "What haven't I turned in?"
        - "Which assignments still need to be submitted?"
        - "Show me unsubmitted work"

        Args:
            course_identifier: Optional course name, code, or ID.
        """
        course_id, course_name = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(
            course_id, include=["submission"], bucket="unsubmitted"
        )
        title = (
            f"{course_name} - Unsubmitted" if course_id else "All Courses - Unsubmitted"
        )
        return (
            format_assignments(assignments, title)
            if assignments
            else "All assignments submitted! 🎉"
        )

    @tool("get_upcoming_assignments")
    def get_upcoming_assignments(course_identifier: Optional[str] = None) -> str:
        """Get assignments that are due soon (Canvas "upcoming" bucket — typically
        the next ~1 week of assignments that have not yet been submitted).

        Use when the user asks:
        - "What's due this week?"
        - "What do I have coming up?"
        - "What's due soon?"
        - "Upcoming assignments"

        Do NOT use for arbitrary date ranges — use get_assignments_by_date_range.

        Args:
            course_identifier: Optional course name, code, or ID.
        """
        course_id, course_name = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(
            course_id, include=["submission"], bucket="upcoming"
        )
        assignments.sort(key=lambda x: x.get("due_at") or "9999-12-31")
        title = f"{course_name} - Upcoming" if course_id else "All Courses - Upcoming"
        return format_assignments(assignments, title)

    @tool("get_past_assignments")
    def get_past_assignments(course_identifier: Optional[str] = None) -> str:
        """Get assignments whose due date has already passed (submitted or not).

        Use when the user asks:
        - "What assignments have already been due?"
        - "Show me past assignments"
        - "What was due last week?"

        Args:
            course_identifier: Optional course name, code, or ID.
        """
        course_id, course_name = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(
            course_id, include=["submission"], bucket="past"
        )
        assignments.sort(key=lambda x: x.get("due_at") or "0000-01-01", reverse=True)
        title = f"{course_name} - Past" if course_id else "All Courses - Past"
        return format_assignments(assignments, title)

    @tool("get_future_assignments")
    def get_future_assignments(course_identifier: Optional[str] = None) -> str:
        """Get assignments whose due date is in the future (not yet due).

        Use when the user asks:
        - "What's coming up later?"
        - "Show me future assignments"
        - "What will be due later in the semester?"

        Args:
            course_identifier: Optional course name, code, or ID.
        """
        course_id, course_name = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(course_id, bucket="future")
        assignments.sort(key=lambda x: x.get("due_at") or "9999-12-31")
        title = f"{course_name} - Future" if course_id else "All Courses - Future"
        return format_assignments(assignments, title)

    @tool("get_ungraded_assignments")
    def get_ungraded_assignments(course_identifier: Optional[str] = None) -> str:
        """Get assignments that have been submitted but have NOT been graded yet
        by the instructor.

        Use when the user asks:
        - "What's still being graded?"
        - "Which assignments haven't been graded?"
        - "Am I waiting on any grades?"

        Args:
            course_identifier: Optional course name, code, or ID.
        """
        course_id, course_name = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(
            course_id, include=["submission"], bucket="ungraded"
        )
        title = (
            f"{course_name} - Awaiting Grade"
            if course_id
            else "All Courses - Awaiting Grade"
        )
        return (
            format_assignments(assignments, title)
            if assignments
            else "No assignments awaiting grading."
        )

    @tool("get_assignment_submission_status")
    def get_assignment_submission_status(
        assignment_name: str, course_identifier: Optional[str] = None
    ) -> str:
        """Check the submission status of ONE specific assignment: whether it was
        submitted, when, if it was late, and the grade/score/feedback.

        Use when the user asks:
        - "Did I submit [assignment]?"
        - "What grade did I get on [assignment]?"
        - "Is [assignment] late?"
        - "Any feedback on [assignment]?"

        Args:
            assignment_name: Full or partial name of the assignment.
            course_identifier: Optional course name, code, or ID.
        """
        course_id, _ = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(
            course_id, include=["submission"]
        )

        needle = assignment_name.lower()
        for a in assignments:
            if needle in a.get("name", "").lower():
                submission = a.get("submission", {})
                lines = [f"# Submission Status: {a.get('name')}\n"]
                lines.append(
                    f"**Status:** {submission.get('workflow_state', 'Not submitted')}"
                )

                if submission.get("submitted_at"):
                    lines.append(f"**Submitted At:** {submission['submitted_at']}")
                if submission.get("late"):
                    lines.append("**⚠️ LATE SUBMISSION**")
                if submission.get("grade"):
                    lines.append(f"**Grade:** {submission['grade']}")
                if submission.get("score") is not None:
                    pts = a.get("points_possible", "?")
                    lines.append(f"**Score:** {submission['score']}/{pts}")
                if submission.get("graded_at"):
                    lines.append(f"**Graded At:** {submission['graded_at']}")

                comments = submission.get("submission_comments", [])
                if comments:
                    lines.append("\n## Feedback")
                    for c in comments:
                        lines.append(
                            f"**{c.get('author_name', 'Instructor')}:** {c.get('comment', '')}"
                        )

                return "\n".join(lines)

        return f"Assignment '{assignment_name}' not found."

    @tool("get_assignments_by_date_range")
    def get_assignments_by_date_range(
        start_date: str,
        end_date: str,
        course_identifier: Optional[str] = None,
    ) -> str:
        """Get assignments whose due date falls within a specific date range.

        Use when the user asks:
        - "What's due between [date] and [date]?"
        - "Show me assignments for next month"
        - "What's due in the first week of December?"

        Do NOT use for simple "upcoming this week" — use get_upcoming_assignments.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            course_identifier: Optional course name, code, or ID.
        """
        start_dt = helper.parse_date(start_date)
        end_dt = helper.parse_date(end_date)
        if not start_dt or not end_dt:
            return "Invalid date format. Please use YYYY-MM-DD format."

        course_id, course_name = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(course_id)

        filtered = []
        for a in assignments:
            due_dt = helper.parse_date(a.get("due_at"))
            if due_dt and start_dt <= due_dt <= end_dt:
                filtered.append(a)

        filtered.sort(key=lambda x: x.get("due_at") or "9999-12-31")
        title = f"Assignments Due {start_date} to {end_date}"
        if course_id:
            title += f" - {course_name}"
        return format_assignments(filtered, title)

    @tool("search_assignments")
    def search_assignments(
        search_term: str, course_identifier: Optional[str] = None
    ) -> str:
        """Search for assignments by title using Canvas server-side search.

        Use when the user asks:
        - "Find the assignment called [name]"
        - "Search for [keyword] in assignments"
        - "Is there an assignment about [topic]?"

        Args:
            search_term: Text to match in assignment titles.
            course_identifier: Optional course name, code, or ID.
        """
        course_id, course_name = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(
            course_id, search_term=search_term
        )
        title = f"Search: '{search_term}'"
        if course_id:
            title = f"{course_name} - {title}"
        return format_assignments(assignments, title)

    @tool("get_assignments_by_type")
    def get_assignments_by_type(
        assignment_type: str, course_identifier: Optional[str] = None
    ) -> str:
        """Get assignments filtered by submission type.

        Supported types: "online_quiz", "discussion_topic", "online_upload",
        "online_text_entry", "external_tool", "media_recording", "on_paper".

        Use when the user asks:
        - "Show me all quizzes"           → assignment_type="online_quiz"
        - "List my discussions"           → assignment_type="discussion_topic"
        - "What uploads do I have?"       → assignment_type="online_upload"
        - "Show me external tool assignments" → assignment_type="external_tool"

        Args:
            assignment_type: One of the Canvas submission types listed above.
            course_identifier: Optional course name, code, or ID.
        """
        course_id, course_name = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(course_id)
        filtered = helper.filter_by_submission_type(assignments, assignment_type)

        type_labels = {
            "online_quiz": "Quizzes",
            "discussion_topic": "Discussions",
            "online_upload": "File Uploads",
            "online_text_entry": "Text Entries",
            "external_tool": "External Tools",
            "media_recording": "Media Recordings",
            "on_paper": "On Paper",
        }
        label = type_labels.get(assignment_type, assignment_type)
        scope = course_name if course_id else "All Courses"
        return format_assignments(filtered, f"{scope} - {label}")

    @tool("get_peer_review_assignments")
    def get_peer_review_assignments(course_identifier: Optional[str] = None) -> str:
        """Get assignments that require peer reviews.

        Use when the user asks:
        - "Do I have any peer reviews?"
        - "Which assignments need peer review?"

        Args:
            course_identifier: Optional course name, code, or ID.
        """
        course_id, course_name = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(course_id)

        peer_reviews = [a for a in assignments if a.get("peer_reviews")]

        scope = course_name if course_id else "All Courses"
        lines = [f"# Peer Review Assignments - {scope}\n"]

        if not peer_reviews:
            lines.append("No peer review assignments found.")
        else:
            for i, a in enumerate(peer_reviews, 1):
                auto = a.get("automatic_peer_reviews", False)
                lines.append(f"{i}. **{a.get('name', 'Unnamed')}**")
                lines.append(f"   - **Due:** {a.get('due_at', 'No due date')}")
                lines.append(f"   - **Points:** {a.get('points_possible', 'N/A')}")
                lines.append(f"   - **Auto-assigned:** {'Yes' if auto else 'No'}")
                if auto:
                    lines.append(
                        f"   - **Reviews Required:** {a.get('peer_review_count', 'N/A')}"
                    )
                lines.append("")

        return "\n".join(lines)

    return [
        get_overdue_assignments,
        get_unsubmitted_assignments,
        get_upcoming_assignments,
        get_past_assignments,
        get_future_assignments,
        get_ungraded_assignments,
        get_assignment_submission_status,
        get_assignments_by_date_range,
        search_assignments,
        get_assignments_by_type,
        get_peer_review_assignments,
    ]
