"""Grade and statistics related Canvas tools."""

from typing import Optional
from langchain.tools import tool
from .base import CanvasToolsHelper
from .formatters import format_grades


def create_grade_tools(helper: CanvasToolsHelper, canvas_repo):
    """Create grade-related Canvas tools."""

    @tool("get_course_grades")
    def get_course_grades(course_identifier: Optional[str] = None) -> str:
        """Get the student's current overall grades (percentage and letter grade)
        for a specific course or all courses.

        This returns the *course-level* grade, NOT individual assignment scores.
        For individual assignment scores use get_assignment_submission_status.

        Use when the user asks:
        - "What's my grade in [course]?"
        - "Show me my grades"
        - "How am I doing grade-wise?"
        - "What's my GPA / average?"

        Args:
            course_identifier: Optional course name, code, or ID.
                             If omitted returns grades for ALL courses.
        """
        if course_identifier:
            course_id, error_or_name = helper.resolve_course_id(course_identifier)
            if course_id is None:
                return error_or_name

            grades = canvas_repo.get_all_grades()
            for grade in grades:
                if grade.get("course") == error_or_name:
                    score = grade.get("current_score", "N/A")
                    letter = grade.get("current_grade", "")
                    return f"Grade for {error_or_name}: {score}%" + (
                        f" ({letter})" if letter else ""
                    )
            return f"No grade information available for {error_or_name}."

        grades = canvas_repo.get_all_grades()
        return format_grades(grades)

    @tool("get_assignment_score_statistics")
    def get_assignment_score_statistics(
        assignment_name: str, course_identifier: Optional[str] = None
    ) -> str:
        """Get class-wide score statistics for ONE specific assignment and
        compare the student's performance against the class average, median,
        and quartiles.

        Use when the user asks:
        - "How did I do compared to the class on [assignment]?"
        - "What's the class average on [assignment]?"
        - "Show me the stats for [assignment]"

        Args:
            assignment_name: Full or partial name of the assignment.
            course_identifier: Optional course name, code, or ID.
        """
        course_id, _ = helper.resolve_course_id(course_identifier)
        assignments = helper.get_assignments_for_courses(
            course_id, include=["score_statistics", "submission"]
        )

        needle = assignment_name.lower()
        for a in assignments:
            if needle in a.get("name", "").lower():
                stats = a.get("score_statistics")
                submission = a.get("submission", {})

                lines = [f"# Performance Comparison: {a.get('name')}\n"]

                if not stats:
                    lines.append(
                        "Statistics not available (requires at least 5 graded "
                        "submissions or instructor has disabled statistics)."
                    )
                else:
                    lines.append(f"**Class Mean (Average):** {stats.get('mean', 'N/A')}")
                    lines.append(f"**Class Median:** {stats.get('median', 'N/A')}")
                    lines.append(f"**Class High Score:** {stats.get('max', 'N/A')}")
                    lines.append(f"**Class Low Score:** {stats.get('min', 'N/A')}")
                    lines.append(f"**Upper Quartile (75th):** {stats.get('upper_q', 'N/A')}")
                    lines.append(f"**Lower Quartile (25th):** {stats.get('lower_q', 'N/A')}")

                if submission.get("score") is not None:
                    your_score = submission["score"]
                    lines.append("\n## Your Performance")
                    lines.append(f"**Your Score:** {your_score}")

                    if stats:
                        mean = stats.get("mean")
                        median = stats.get("median")
                        upper_q = stats.get("upper_q")
                        lower_q = stats.get("lower_q")

                        if mean:
                            diff = your_score - mean
                            if diff > 0:
                                lines.append(f"**vs. Average:** {diff:.2f} points above 📈")
                            elif diff < 0:
                                lines.append(f"**vs. Average:** {abs(diff):.2f} points below 📉")
                            else:
                                lines.append("**vs. Average:** Right at the average")

                        if upper_q and lower_q and median:
                            if your_score >= upper_q:
                                lines.append("**Percentile:** Top 25% of the class! 🌟")
                            elif your_score >= median:
                                lines.append("**Percentile:** Above median (50th–75th)")
                            elif your_score >= lower_q:
                                lines.append("**Percentile:** Below median (25th–50th)")
                            else:
                                lines.append("**Percentile:** Bottom 25%")

                return "\n".join(lines)

        return f"Assignment '{assignment_name}' not found."

    @tool("get_grade_impact_forecast")
    def get_grade_impact_forecast(course_identifier: str) -> str:
        """Calculate how upcoming un-graded assignments could affect the final
        course grade at different performance levels (100 %, 90 %, 80 %, …).

        Use when the user asks:
        - "What do I need to get an A in [course]?"
        - "How will my grade change if I ace the rest?"
        - "What's my grade forecast?"
        - "Can I still pass [course]?"

        Args:
            course_identifier: Course name, code, or ID (required).
        """
        course_id, course_name = helper.resolve_course_id(course_identifier)
        if not course_id:
            return "Please specify a valid course."

        assignments = canvas_repo.get_assignments(course_id, include=["submission"])

        total_earned = 0
        total_possible = 0
        pending_points = 0

        for a in assignments:
            pts = a.get("points_possible", 0)
            score = (a.get("submission") or {}).get("score")
            if score is not None:
                total_earned += score
                total_possible += pts
            elif pts > 0:
                pending_points += pts

        current_grade = (
            (total_earned / total_possible * 100) if total_possible > 0 else 0
        )
        total_with_pending = total_possible + pending_points

        lines = [f"# Grade Impact Forecast – {course_name}\n"]
        lines.append("## Current Status")
        lines.append(f"**Current Grade:** {current_grade:.2f}% ({total_earned}/{total_possible} pts)")
        lines.append(f"**Pending Assignments:** {pending_points} pts\n")
        lines.append("## Forecast Scenarios\n")

        for label, mult in [
            ("Perfect (100%)", 1.0),
            ("Excellent (90%)", 0.9),
            ("Good (80%)", 0.8),
            ("Average (70%)", 0.7),
            ("Passing (60%)", 0.6),
        ]:
            proj = total_earned + pending_points * mult
            pct = (proj / total_with_pending * 100) if total_with_pending > 0 else 0
            lines.append(f"**{label}:** {pct:.2f}%")

        lines.append(
            f"\n*Note: assumes all pending assignments total {pending_points} pts.*"
        )
        return "\n".join(lines)

    return [
        get_course_grades,
        get_assignment_score_statistics,
        get_grade_impact_forecast,
    ]
