"""Analysis and planning tools for Canvas assignments."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from langchain.tools import tool

from .base import CanvasToolsHelper

_logger = logging.getLogger(__name__)


def create_analysis_tools(
    helper: CanvasToolsHelper, canvas_repo, google_calendar_helper=None
):
    """Create analysis and planning tools."""
    _ = canvas_repo

    @tool("create_weekly_study_plan")
    def create_weekly_study_plan(course_identifier: Optional[str] = None) -> str:
        """Create a personalized study plan for the CURRENT WEEK based on upcoming
        Canvas assignments. Returns a formatted plan WITHOUT modifying Google Calendar.

        Use when the user asks:
        - "Create a study plan for this week"
        - "Plan my week"
        - "What should I study this week?"
        - "Help me organize my week"

        Args:
            course_identifier: Optional course to focus on. If omitted, includes all courses.

        Returns:
            A formatted study plan with suggested study times.
            The user can then confirm to add these sessions to Google Calendar.
        """
        try:
            now = datetime.now(timezone.utc)
            weekday = now.weekday()
            week_start = now - timedelta(days=weekday)
            week_end = week_start + timedelta(days=6)

            course_id, course_name = helper.resolve_course_id(course_identifier)
            assignments = helper.get_assignments_for_courses(
                course_id, include=["submission"], bucket="upcoming"
            )

            this_week = []
            for a in assignments:
                due_dt = helper.parse_date(a.get("due_at"))
                if due_dt and week_start <= due_dt <= week_end:
                    submission = a.get("submission", {})
                    if submission.get("workflow_state") != "submitted":
                        this_week.append(a)

            if not this_week:
                return (
                    f"No upcoming assignments due this week "
                    f"({week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')})!"
                )

            this_week.sort(key=lambda x: x.get("due_at", "9999-12-31"))

            def estimate_time(a):
                """Estimate study time in hours."""
                points = a.get("points_possible", 0)
                stypes = a.get("submission_types", [])
                desc = a.get("description", "")

                if "online_quiz" in stypes:
                    base = 0.5
                elif "discussion_topic" in stypes:
                    base = 0.75
                elif "online_upload" in stypes or "online_text_entry" in stypes:
                    base = 2.0
                else:
                    base = 1.0

                complexity = (points * 0.02) if points > 0 else 0
                desc_factor = 1.0 if desc and len(desc.split()) > 500 else 0
                return round((base + complexity + desc_factor) * 2) / 2

            lines = [
                f"#Study Plan for Week of {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}\n"
            ]
            lines.append(
                f"**Course Focus:** {course_name if course_id else 'All Courses'}\n"
            )
            lines.append("## Recommended Study Sessions\n")

            total_hours = 0

            for i, a in enumerate(this_week, 1):
                name = a.get("name", "Unnamed Assignment")
                due_dt = helper.parse_date(a.get("due_at"))
                study_hours = estimate_time(a)
                total_hours += study_hours

                if due_dt:
                    study_date = due_dt - timedelta(days=1)
                    if study_date < now:
                        study_date = now + timedelta(hours=2)

                    study_start = study_date.replace(
                        hour=14, minute=0, second=0, microsecond=0
                    )

                    course_prefix = a.get("_course_name", "")

                    lines.append(
                        f"### {i}. {name}\n"
                        f"- **Course:** {course_prefix}\n"
                        f"- **Suggested Time:** {study_start.strftime('%A, %b %d at %I:%M %p')}\n"
                        f"- **Duration:** {study_hours}h\n"
                        f"- **Due:** {due_dt.strftime('%A, %b %d at %I:%M %p')}\n"
                        f"- **Points:** {a.get('points_possible', 'N/A')}\n"
                    )

            lines.append(f"\n## Summary\n")
            lines.append(f"- **Total Study Sessions:** {len(this_week)}")
            lines.append(f"- **Total Study Time:** {total_hours}h")
            lines.append(f"- **Assignments Covered:** {len(this_week)}")

            if google_calendar_helper:
                lines.append(
                    f"\n---\n\n"
                    f"**Want to add these sessions to your Google Calendar?**\n"
                    f'Just ask: *"Add these study sessions to my calendar"* and I\'ll schedule them for you!'
                )
            else:
                lines.append(
                    f"\n---\n\n"
                    f"ℹConnect your Google Calendar to automatically schedule these sessions."
                )

            return "\n".join(lines)

        except Exception as e:
            _logger.error("create_weekly_study_plan failed: %s", e, exc_info=True)
            return f"❌ Failed to create study plan: {e}"

    @tool("get_workload_summary")
    def get_workload_summary(
        days_ahead: int = 7, course_identifier: Optional[str] = None
    ) -> str:
        """Get a day-by-day breakdown of upcoming assignments with total points
        per day, so the student can plan their week.

        Use when the user asks:
        - "How heavy is my workload this week?"
        - "Show me what's due day by day"
        - "Plan my week"
        - "How many assignments do I have each day?"

        Do NOT use for a simple list of upcoming assignments
        — use get_upcoming_assignments instead.

        Args:
            days_ahead: Number of days to look ahead (default 7).
            course_identifier: Optional course name, code, or ID.
        """
        course_id, _ = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(course_id, bucket="upcoming")

        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=days_ahead)

        upcoming = []
        for a in assignments:
            due_dt = helper.parse_date(a.get("due_at"))
            if due_dt:
                if due_dt.tzinfo is None:
                    due_dt = due_dt.replace(tzinfo=timezone.utc)
                if now <= due_dt <= end_date:
                    upcoming.append(a)

        by_day: dict[str, list] = {}
        for a in upcoming:
            due_dt = helper.parse_date(a.get("due_at"))
            if due_dt:
                if due_dt.tzinfo is None:
                    due_dt = due_dt.replace(tzinfo=timezone.utc)
                day_key = due_dt.strftime("%Y-%m-%d (%A)")
                by_day.setdefault(day_key, []).append(a)

        lines = [f"# Workload Summary – Next {days_ahead} Days\n"]

        if not by_day:
            lines.append("No assignments due in this period!")
        else:
            for day in sorted(by_day.keys()):
                day_assignments = by_day[day]
                total_pts = sum(a.get("points_possible", 0) for a in day_assignments)
                lines.append(f"## {day}")
                lines.append(
                    f"**Total Points:** {total_pts} | "
                    f"**Assignments:** {len(day_assignments)}\n"
                )
                for a in day_assignments:
                    lines.append(
                        f"- **{a.get('name', 'Unnamed')}** "
                        f"({a.get('points_possible', 'N/A')} pts)"
                    )
                lines.append("")

        return "\n".join(lines)

    @tool("get_assignment_priority_list")
    def get_assignment_priority_list(course_identifier: Optional[str] = None) -> str:
        """Rank pending assignments by urgency and importance using a weighted
        priority score: due-date proximity (40 %), points possible (30 %),
        and submission status (30 %).  Shows the top 15.

        Use when the user asks:
        - "What should I work on first?"
        - "Prioritize my assignments"
        - "What's most urgent?"
        - "Rank my assignments"

        Args:
            course_identifier: Optional course name, code, or ID.
        """
        course_id, _ = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(
            course_id, include=["submission"]
        )

        pending = [
            a
            for a in assignments
            if (a.get("submission") or {}).get("workflow_state", "unsubmitted")
            in ("unsubmitted", "submitted")
        ]

        def priority_score(a):
            score = 0
            days = helper.days_until_due(a.get("due_at"))
            if days < 0:
                score += 100
            elif days <= 1:
                score += 80
            elif days <= 3:
                score += 60
            elif days <= 7:
                score += 40
            else:
                score += max(0, 40 - days)

            pts = a.get("points_possible", 0)
            score += min(30, pts * 0.3)

            ws = (a.get("submission") or {}).get("workflow_state", "unsubmitted")
            score += 30 if ws == "unsubmitted" else 15

            return score

        pending.sort(key=priority_score, reverse=True)

        lines = ["# Priority Assignment List\n"]
        lines.append("Ranked by urgency (due date), importance (points), and status.\n")

        if not pending:
            lines.append("No pending assignments! 🎉")
        else:
            for i, a in enumerate(pending[:15], 1):
                days = helper.days_until_due(a.get("due_at"))
                urgency = "OVERDUE" if days < 0 else f"⏰ {days} days"
                ps = priority_score(a)
                lines.append(
                    f"{i}. **{a.get('name', 'Unnamed')}** – {urgency} | "
                    f"{a.get('points_possible', 'N/A')} pts | "
                    f"Priority: {ps:.0f}/100 | Due: {a.get('due_at', 'N/A')}"
                )

        return "\n".join(lines)

    @tool("get_study_time_estimate")
    def get_study_time_estimate(
        assignment_name: str, course_identifier: Optional[str] = None
    ) -> str:
        """Estimate how long the student should spend on a specific assignment
        based on its type, point value, and description length.

        Use when the user asks:
        - "How long will [assignment] take?"
        - "Estimate study time for [assignment]"
        - "How much time should I plan for [assignment]?"

        Args:
            assignment_name: Full or partial name of the assignment.
            course_identifier: Optional course name, code, or ID.
        """
        course_id, _ = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(course_id)

        needle = assignment_name.lower()
        for a in assignments:
            if needle in a.get("name", "").lower():
                name = a.get("name", "Unnamed")
                points = a.get("points_possible", 0)
                stypes = a.get("submission_types", [])
                desc = a.get("description", "")

                if "online_quiz" in stypes:
                    base = 30
                elif "discussion_topic" in stypes:
                    base = 45
                elif "online_upload" in stypes or "online_text_entry" in stypes:
                    base = 120
                elif "external_tool" in stypes:
                    base = 60
                else:
                    base = 60

                complexity_adj = points * 2 if points > 0 else 0
                desc_adj = 60 if desc and len(desc.split()) > 500 else 0
                total = round((base + complexity_adj + desc_adj) / 15) * 15

                lines = [f"# Study Time Estimate: {name}\n"]
                lines.append(f"**Estimated Time:** {total} min (~{total / 60:.1f} h)")
                lines.append(f"**Points Possible:** {points}")
                lines.append(f"**Assignment Type:** {', '.join(stypes)}\n")
                lines.append("## Breakdown")
                lines.append(f"- Base time for type: {base} min")
                if complexity_adj:
                    lines.append(
                        f"- Complexity (based on points): +{complexity_adj} min"
                    )
                if desc_adj:
                    lines.append("- Detailed instructions: +60 min")
                lines.append(
                    "\n*Actual time may vary based on your familiarity with the topic.*"
                )
                return "\n".join(lines)

        return f"Assignment '{assignment_name}' not found."

    return [
        get_workload_summary,
        get_assignment_priority_list,
        get_study_time_estimate,
        create_weekly_study_plan,
    ]
