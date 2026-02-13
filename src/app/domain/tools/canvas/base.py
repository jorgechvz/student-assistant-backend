"""Canvas tools helper class with shared utilities."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class CanvasToolsHelper:
    """Shared helper class for Canvas tools.

    Provides course resolution, date arithmetic, and a unified method to
    fetch assignments from one or all courses using Canvas API parameters
    (``bucket``, ``include``, ``search_term``) instead of local filtering.
    """

    def __init__(self, canvas_repo):
        self.canvas_repo = canvas_repo
        self._courses_cache: Optional[List[Dict[str, Any]]] = None

    def get_courses(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """Get active courses with caching."""
        if self._courses_cache is None or refresh:
            self._courses_cache = self.canvas_repo.get_active_courses()
        return self._courses_cache

    def find_course_by_name_or_code(self, search_term: str) -> Optional[Dict[str, Any]]:
        """Case-insensitive partial match on course name or code."""
        courses = self.get_courses()
        s = search_term.lower()
        for c in courses:
            name = c.get("name", "").lower()
            code = c.get("course_code", "").lower()
            if s in name or s in code or name in s or code in s:
                return c
        return None

    def resolve_course_id(
        self, course_identifier: Optional[str] = None
    ) -> tuple[Optional[int], str]:
        """Resolve *course_identifier* → ``(course_id, course_name)``.

        Returns ``(None, "")`` when no identifier is given.
        Returns ``(None, error_message)`` when the course cannot be found.
        """
        if not course_identifier:
            return None, ""

        try:
            cid = int(course_identifier)
            cname = self.canvas_repo.get_course_name(cid)
            if cname:
                return cid, cname
        except (ValueError, TypeError):
            pass

        course = self.find_course_by_name_or_code(course_identifier)
        if course:
            return course.get("id"), course.get("name", "Unknown Course")

        course_list = "\n".join(
            f"  • {c.get('name')} ({c.get('course_code')})" for c in self.get_courses()
        )
        return (
            None,
            f"Could not find course '{course_identifier}'. "
            f"Available courses:\n{course_list}",
        )

    def get_assignments_for_courses(
        self,
        course_id: Optional[int] = None,
        include: Optional[List[str]] = None,
        bucket: Optional[str] = None,
        search_term: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch assignments from one course or all active courses.

        The ``bucket`` parameter is passed straight to the Canvas API so
        the server does the filtering (past | overdue | undated | ungraded |
        unsubmitted | upcoming | future).  No local re-filtering needed.
        """
        if course_id:
            return self.canvas_repo.get_assignments(
                course_id, include=include, bucket=bucket, search_term=search_term
            )

        all_assignments: List[Dict[str, Any]] = []
        for course in self.get_courses():
            cid = course["id"]
            cname = course.get("name", f"Course {cid}")
            assignments = self.canvas_repo.get_assignments(
                cid, include=include, bucket=bucket, search_term=search_term
            )
            for a in assignments:
                a["_course_name"] = cname
            all_assignments.extend(assignments)
        return all_assignments

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """Parse a date string to a timezone-aware UTC datetime."""
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue
        return None

    @staticmethod
    def days_until_due(due_date_str: str) -> int:
        """Days until due. Returns 999 if unknown, negative if overdue."""
        dt = CanvasToolsHelper.parse_date(due_date_str)
        if not dt:
            return 999
        return (dt - datetime.now(timezone.utc)).days

    @staticmethod
    def is_overdue(due_date_str: str) -> bool:
        """Check if an assignment is past its due date."""
        dt = CanvasToolsHelper.parse_date(due_date_str)
        return dt is not None and dt < datetime.now(timezone.utc)

    @staticmethod
    def filter_by_submission_type(
        assignments: List[Dict[str, Any]], submission_type: str
    ) -> List[Dict[str, Any]]:
        """Filter assignments by submission_types field."""
        return [
            a for a in assignments if submission_type in a.get("submission_types", [])
        ]
