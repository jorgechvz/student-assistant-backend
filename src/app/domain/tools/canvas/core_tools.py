"""Core Canvas tools – courses, basic assignments, announcements, syllabus."""

from typing import Optional
from langchain.tools import tool
from .base import CanvasToolsHelper
from .formatters import (
    format_course_list,
    format_assignments,
    format_assignment_detailed,
)


def create_core_tools(helper: CanvasToolsHelper, canvas_repo):
    """Create core Canvas tools."""

    @tool("get_current_courses")
    def get_current_courses() -> str:
        """List every active course the student is currently enrolled in on Canvas LMS.

        Returns course name, course code, ID, and start date for each course.

        Use when the user asks:
        - "What courses am I taking?"
        - "Show me my classes"
        - "List my courses"
        """
        courses = helper.get_courses(refresh=True)
        return format_course_list(courses)

    @tool("get_all_assignments")
    def get_all_assignments(course_identifier: Optional[str] = None) -> str:
        """Get every assignment (past, current, and future) for a specific course
        or all courses. Returns the complete list regardless of status.

        Use when the user asks:
        - "Show me all my assignments"
        - "What assignments do I have in [course]?"
        - "List every assignment"

        Do NOT use this for filtered views (overdue, upcoming, etc.)
        — use the specific bucket tools instead.

        Args:
            course_identifier: Optional course name, code, or ID.
                             If omitted returns assignments from all courses.
        """
        course_id, course_name = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(course_id)

        if course_id:
            return format_assignments(assignments, course_name)

        if not assignments:
            return "No assignments found."

        by_course: dict[str, list] = {}
        for a in assignments:
            cname = a.get("_course_name", "Unknown")
            by_course.setdefault(cname, []).append(a)

        parts = [
            format_assignments(assgns, cname) for cname, assgns in by_course.items()
        ]
        return "\n\n---\n\n".join(parts)

    @tool("get_assignment_details")
    def get_assignment_details(
        assignment_name: str, course_identifier: Optional[str] = None
    ) -> str:
        """Get full details for ONE specific assignment: description, rubric,
        due/unlock/lock dates, submission types, and your submission status.

        Use when the user asks:
        - "Tell me about the [assignment name] assignment"
        - "What are the details of [assignment]?"
        - "Show me the rubric for [assignment]"
        - "Can you describe [assignment]?"

        Args:
            assignment_name: Full or partial name of the assignment to look up.
            course_identifier: Optional course name, code, or ID.
        """
        course_id, course_name = helper.resolve_course_id(course_identifier)

        search_results = helper.get_assignments_for_courses(
            course_id, include=["submission"], search_term=assignment_name
        )

        needle = assignment_name.lower()
        for a in search_results:
            if needle in a.get("name", "").lower():
                return format_assignment_detailed(a)

        all_assignments = helper.get_assignments_for_courses(
            course_id, include=["submission"]
        )

        for a in all_assignments:
            if needle in a.get("name", "").lower():
                return format_assignment_detailed(a)

        scope = f"in {course_name}" if course_id else "in all your courses"

        similar = []
        for a in all_assignments:
            name = a.get("name", "")
            if any(word.lower() in name.lower() for word in assignment_name.split()):
                similar.append(f"  • {name}")

        if similar:
            similar_list = "\n".join(similar[:5])
            return (
                f"Assignment '{assignment_name}' not found {scope}.\n\n"
                f"Did you mean one of these?\n{similar_list}\n\n"
                f"Try asking: 'Can you describe [exact assignment name]?'"
            )

        return (
            f"Assignment '{assignment_name}' not found {scope}.\n\n"
            f"Possible reasons:\n"
            f"  • The assignment hasn't been published yet\n"
            f"  • It's only visible to specific groups/sections\n"
            f"  • The name is spelled differently\n\n"
            f"Try using: 'Show me all assignments in {course_name or 'my courses'}' "
            f"to see the full list."
        )

    @tool("get_course_syllabus")
    def get_course_syllabus(course_identifier: str) -> str:
        """Retrieve the syllabus content for a specific course.

        Use when the user asks:
        - "Show me the syllabus for [course]"
        - "What does the syllabus say?"

        Args:
            course_identifier: Course name, code, or ID (required).
        """
        course_id, error_or_name = helper.resolve_course_id(course_identifier)
        if course_id is None:
            return error_or_name

        result = canvas_repo.get_course_syllabus_by_id(course_id)
        if result.get("error"):
            return result["error"]

        syllabus = result.get("syllabus", "")
        if not syllabus or syllabus.strip() == "":
            return f"No syllabus available for {error_or_name}."

        return f"Syllabus for {error_or_name}:\n\n{syllabus}"

    @tool("get_course_announcements")
    def get_course_announcements(course_identifier: Optional[str] = None) -> str:
        """Get recent announcements posted by instructors.

        Use when the user asks:
        - "Are there any announcements?"
        - "What did my professor post?"
        - "Show announcements for [course]"

        Args:
            course_identifier: Optional course name, code, or ID.
                             If omitted returns announcements from all courses.
        """
        course_id = None
        if course_identifier:
            course_id, error_or_name = helper.resolve_course_id(course_identifier)
            if course_id is None:
                return error_or_name

        announcements = canvas_repo.get_announcements(course_id)
        if not announcements:
            return "No recent announcements."

        lines = ["Recent announcements:\n"]
        for ann in announcements:
            course = ann.get("course", "")
            title = ann.get("title", "No title")
            posted = ann.get("posted_at", "")
            message = ann.get("message", "")
            html_url = ann.get("html_url", "")

            lines.append(f"\n{course} - {title}")
            if posted:
                lines.append(f"   Posted: {posted}")
            if message:
                preview = message[:500] + "..." if len(message) > 500 else message
                lines.append(f"   {preview}")
            if html_url:
                lines.append(f"   You can view it here: {html_url}")

        return "\n".join(lines)

    return [
        get_current_courses,
        get_all_assignments,
        get_assignment_details,
        get_course_syllabus,
        get_course_announcements,
    ]
