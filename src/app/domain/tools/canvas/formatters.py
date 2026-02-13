"""Formatting utilities for Canvas tools."""

import re
from typing import Any, Dict


def format_course_list(courses: list[Dict[str, Any]]) -> str:
    """Format the list of courses into a readable string."""
    if not courses:
        return "You are not enrolled in any active courses."

    result = ["Your current active courses:\n"]
    for course in courses:
        name = course.get("name", "Unnamed")
        code = course.get("course_code", "N/A")
        course_id = course.get("id", "N/A")
        start_date = course.get("start_at", "N/A")
        result.append(
            f"  • {name} ({code}) - ID: {course_id}, Start Date: {start_date}"
        )

    return "\n".join(result)


def format_assignments(assignments: list[Dict[str, Any]], course_name: str) -> str:
    """Format assignments for readable output."""
    if not assignments:
        return f"No assignments found for {course_name}."

    result = [f"# Current Assignments for {course_name}\n"]

    for i, assignment in enumerate(assignments, 1):
        name = assignment.get("name", "Unnamed Assignment")
        due_date = assignment.get("due_at", "No due date")
        points = assignment.get("points_possible", "N/A")
        description = assignment.get("description", "")
        url = assignment.get("html_url", "")

        clean_desc = ""
        if description:
            clean_desc = description.replace("\n", " ").strip()
            clean_desc = re.sub(r"<[^>]+>", "", clean_desc)
            if len(clean_desc) > 150:
                clean_desc = clean_desc[:150] + "..."

        result.append(f"{i}. **{name}**")
        result.append(f"   - **Due:** {due_date}")
        result.append(f"   - **Points:** {points}")

        if clean_desc:
            result.append(f"   - **Overview:** {clean_desc}")

        if url:
            result.append(f"   - [View Assignment]({url})")

        result.append("")

    return "\n".join(result)


def format_assignment_detailed(assignment: Dict[str, Any]) -> str:
    """Format detailed assignment information."""
    name = assignment.get("name", "Unnamed Assignment")
    description = assignment.get("description", "No description")
    due_date = assignment.get("due_at", "No due date")
    unlock_date = assignment.get("unlock_at", "Not specified")
    lock_date = assignment.get("lock_at", "Not specified")
    points = assignment.get("points_possible", "N/A")
    submission_types = ", ".join(assignment.get("submission_types", []))
    url = assignment.get("html_url", "")
    rubric = assignment.get("rubric", [])

    result = [f"# {name}\n"]
    result.append(f"**Points Possible:** {points}")
    result.append(f"**Due Date:** {due_date}")
    result.append(f"**Unlock Date:** {unlock_date}")
    result.append(f"**Lock Date:** {lock_date}")
    result.append(f"**Submission Types:** {submission_types}")
    result.append(f"\n## Description\n{description}\n")

    if url:
        result.append(f"[View Assignment in Canvas]({url})")

    if rubric:
        result.append("\n## Grading Rubric")
        for criterion in rubric:
            crit_desc = criterion.get("description", "No description")
            ratings = criterion.get("ratings", [])
            result.append(f"\n### {crit_desc}")
            for rating in ratings:
                points = rating.get("points", "N/A")
                rating_desc = rating.get("description", "No description")
                long_rating_desc = rating.get("long_description", "No description")
                result.append(
                    f"  - {points} points: {rating_desc} - {long_rating_desc}"
                )

    submission = assignment.get("submission")
    if submission:
        result.append(f"\n## Your Submission")
        result.append(f"**Status:** {submission.get('workflow_state', 'Unknown')}")
        if submission.get("submitted_at"):
            result.append(f"**Submitted:** {submission.get('submitted_at')}")
        if submission.get("grade"):
            result.append(f"**Grade:** {submission.get('grade')}")
        if submission.get("score"):
            result.append(f"**Score:** {submission.get('score')}/{points}")

    return "\n".join(result)


def format_grades(grades: list[Dict[str, Any]]) -> str:
    """Format grades list into a readable string."""
    if not grades:
        return "No grade information available for any courses."

    result = ["Current grades for your courses:\n"]
    for grade in grades:
        course = grade.get("course", "Unknown Course")
        score = grade.get("current_score", "N/A")
        letter = grade.get("current_grade", "")
        result.append(f"  • {course}: {score}%" + (f" ({letter})" if letter else ""))

    return "\n".join(result)
