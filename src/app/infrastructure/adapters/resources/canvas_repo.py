"""Canvas LMS Repository Adapter."""

import logging
from typing import Any, Dict, List, Optional
import requests
from requests.exceptions import RequestException


_logger = logging.getLogger(__name__)


class CanvasRepository:
    """Repository adapter for Canvas LMS API."""

    def __init__(self, base_url: str, access_token: str):
        """Initialize Canvas repository.

        Args:
            base_url: Canvas LMS base URL (e.g., 'https://canvas.instructure.com')
            access_token: Canvas API access token for the user
        """
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/api/v1"
        self.access_token = access_token
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
        )

    def _call_api(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> Any:
        """Make a Canvas API request.

        Args:
            endpoint: API endpoint (e.g., '/courses')
            params: Query parameters
            method: HTTP method

        Returns:
            JSON response data

        Raises:
            RequestException: If API call fails
        """
        url = f"{self.api_base}{endpoint}"

        try:
            if method == "GET":
                response = self._session.get(url, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except RequestException as e:
            _logger.error("Canvas API error: %s", str(e))
            raise

    def get_courses(self) -> List[Dict[str, Any]]:
        """Get all courses for the user (active and concluded).

        Returns:
            List of all course objects
        """
        try:
            params = {
                "include[]": ["term", "total_scores"],
            }
            courses = self._call_api("/courses", params)
            return courses

        except RequestException as e:
            _logger.error("Failed to get courses: %s", e)
            return []

    def get_active_courses(self) -> List[Dict[str, Any]]:
        """Get all active courses for the user.

        Returns:
            List of active course objects
        """
        try:
            params = {
                "enrollment_state": "active",
                "include[]": ["term", "concluded"],
            }
            courses = self._call_api("/courses", params)

            active_courses = [
                course for course in courses if not course.get("concluded", False)
            ]

            return active_courses

        except RequestException as e:
            _logger.error("Failed to get active courses: %s", e)
            return []

    def get_course_by_id(self, course_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific course by ID.

        Args:
            course_id: Canvas course ID

        Returns:
            Course object or None if not found
        """
        try:
            course = self._call_api(f"/courses/{course_id}")
            return course
        except RequestException as e:
            _logger.error("Failed to get course %d: %s", course_id, e)
            return None

    def get_course_name(self, course_id: int) -> str:
        """Get course name by ID.

        Args:
            course_id: Canvas course ID

        Returns:
            Course name or empty string if not found
        """
        try:
            course = self._call_api(f"/courses/{course_id}")
            return course.get("name", "")
        except RequestException:
            return ""

    def get_course_syllabus(self, course_name: str) -> Dict[str, Any]:
        """Get syllabus for a course by name or code.

        Args:
            course_name: Course name or code to search for

        Returns:
            Dict with course_name and syllabus, or error message
        """
        try:
            params = {
                "enrollment_state": "active",
                "include[]": ["syllabus_body"],
            }
            courses = self._call_api("/courses", params)

            search_term = course_name.lower()
            for course in courses:
                if course.get("concluded"):
                    continue

                name = course.get("name", "").lower()
                code = course.get("course_code", "").lower()

                if search_term in name or search_term in code:
                    return {
                        "course_name": course.get("name"),
                        "syllabus": course.get("syllabus_body", ""),
                    }

            return {
                "error": f"Course '{course_name}' not found in your active courses."
            }

        except RequestException as e:
            _logger.error("Failed to get course syllabus: %s", e)
            return {"error": "Failed to retrieve syllabus. Please try again."}

    def get_course_syllabus_by_id(self, course_id: int) -> Dict[str, Any]:
        """Get syllabus for a course by ID.

        Args:
            course_id: Canvas course ID
        Returns:
            Dict with course_name and syllabus, or error message
        """
        try:
            course = self._call_api(
                f"/courses/{course_id}", {"include[]": "syllabus_body"}
            )
            return {
                "course_name": course.get("name"),
                "syllabus": course.get("syllabus_body", ""),
            }
        except RequestException as e:
            _logger.error("Failed to get course syllabus by ID: %s", e)
            return {"error": "Failed to retrieve syllabus. Please try again."}

    def get_assignments(
        self,
        course_id: int,
        include: Optional[List[str]] = None,
        search_term: Optional[str] = None,
        bucket: Optional[str] = None,
        assignment_ids: Optional[List[int]] = None,
        order_by: str = "due_at",
        needs_grading_count_by_section: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get assignments for a course with advanced filtering.

        Args:
            course_id: Canvas course ID
            include: Optional list of additional data to include
                     ['submission', 'assignment_visibility', 'all_dates',
                      'overrides', 'observed_users', 'can_edit',
                      'score_statistics', 'ab_guid']
            search_term: Partial title to match
            bucket: Filter by status ['past', 'overdue', 'undated', 'ungraded',
                    'unsubmitted', 'upcoming', 'future']
            assignment_ids: List of specific assignment IDs to retrieve
            order_by: Sort order ['position', 'name', 'due_at']
            needs_grading_count_by_section: Split grading count by section

        Returns:
            List of assignment objects with requested data
        """
        try:
            params = {}

            if include:
                for item in include:
                    params[f"include[]"] = item

            if search_term:
                params["search_term"] = search_term

            if bucket:
                params["bucket"] = bucket

            if assignment_ids:
                params["assignment_ids[]"] = assignment_ids

            if order_by:
                params["order_by"] = order_by

            if needs_grading_count_by_section:
                params["needs_grading_count_by_section"] = True

            assignments = self._call_api(f"/courses/{course_id}/assignments", params)
            _logger.info(
                "Fetched %d assignments for course %d", len(assignments), course_id
            )

            return assignments if isinstance(assignments, list) else []

        except RequestException as e:
            _logger.error("Failed to get assignments for course %d: %s", course_id, e)
            return []

    def get_assignment_by_id(
        self,
        course_id: int,
        assignment_id: int,
        include: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific assignment by ID.

        Args:
            course_id: Canvas course ID
            assignment_id: Assignment ID
            include: Optional list of additional data to include

        Returns:
            Assignment object or None if not found
        """
        try:
            params = {}
            if include:
                for item in include:
                    params[f"include[]"] = item

            assignment = self._call_api(
                f"/courses/{course_id}/assignments/{assignment_id}", params
            )
            return assignment

        except RequestException as e:
            _logger.error(
                "Failed to get assignment %d for course %d: %s",
                assignment_id,
                course_id,
                e,
            )
            return None

    def get_user_assignments(
        self,
        user_id: int,
        course_id: int,
        include: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get assignments for a specific user in a course.

        Args:
            user_id: Canvas user ID
            course_id: Canvas course ID
            include: Optional list of additional data to include

        Returns:
            List of assignment objects
        """
        try:
            params = {}
            if include:
                for item in include:
                    params[f"include[]"] = item

            assignments = self._call_api(
                f"/users/{user_id}/courses/{course_id}/assignments", params
            )
            return assignments if isinstance(assignments, list) else []

        except RequestException as e:
            _logger.error(
                "Failed to get assignments for user %d in course %d: %s",
                user_id,
                course_id,
                e,
            )
            return []

    def get_course_assignments(self, course_id: int) -> List[Dict[str, Any]]:
        """Get all assignments for a course (legacy method).

        Args:
            course_id: Canvas course ID

        Returns:
            List of simplified assignment objects
        """
        try:
            assignments = self.get_assignments(course_id)

            return [
                {
                    "name": a.get("name"),
                    "due_at": a.get("due_at"),
                    "description": a.get("description"),
                    "points_possible": a.get("points_possible"),
                    "html_url": a.get("html_url"),
                }
                for a in assignments
            ]

        except RequestException as e:
            _logger.error("Failed to get course assignments: %s", e)
            return []

    def get_all_upcoming_assignments(self) -> List[Dict[str, Any]]:
        """Get all upcoming assignments across all courses.

        Returns:
            List of assignments with course information
        """
        try:
            courses = self.get_active_courses()

            all_assignments = []
            for course in courses:
                course_id = course.get("id")
                course_name = course.get("name")

                try:
                    assignments = self.get_assignments(
                        course_id,
                        include=["submission"],
                        bucket="upcoming",
                    )

                    for assignment in assignments:
                        if assignment.get("due_at"):
                            all_assignments.append(
                                {
                                    "course": course_name,
                                    "assignment": assignment.get("name"),
                                    "description": assignment.get("description"),
                                    "due_at": assignment.get("due_at"),
                                    "points": assignment.get("points_possible"),
                                    "html_url": assignment.get("html_url"),
                                }
                            )

                except RequestException:
                    continue

            all_assignments.sort(key=lambda x: x.get("due_at", ""))

            return all_assignments

        except RequestException as e:
            _logger.error("Failed to get upcoming assignments: %s", e)
            return []

    def get_all_grades(self) -> List[Dict[str, Any]]:
        """Get current grades for all courses.

        Returns:
            List of grade information by course
        """
        try:
            params = {
                "enrollment_state": "active",
                "include[]": ["total_scores"],
            }
            courses = self._call_api("/courses", params)

            grades = []
            for course in courses:
                if course.get("concluded"):
                    continue

                enrollments = course.get("enrollments", [])
                for enrollment in enrollments:
                    if enrollment.get("type") == "student":
                        grades.append(
                            {
                                "course": course.get("name"),
                                "current_score": enrollment.get(
                                    "computed_current_score"
                                ),
                                "current_grade": enrollment.get(
                                    "computed_current_grade"
                                ),
                                "final_score": enrollment.get("computed_final_score"),
                                "final_grade": enrollment.get("computed_final_grade"),
                            }
                        )

            return grades

        except RequestException as e:
            _logger.error("Failed to get grades: %s", e)
            return []

    def get_announcements(
        self, course_id: Optional[int] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent announcements.

        Args:
            course_id: Optional specific course ID
            limit: Maximum number of announcements to return

        Returns:
            List of announcement objects
        """
        try:
            if course_id:
                endpoint = "/announcements"
                params = {"context_codes[]": f"course_{course_id}", "latest_only": True}
                announcements = self._call_api(endpoint, params)

                return [
                    {
                        "course": "",
                        "title": a.get("title"),
                        "message": a.get("message"),
                        "posted_at": a.get("posted_at"),
                        "html_url": a.get("html_url"),
                    }
                    for a in announcements[:limit]
                ]
            else:
                courses = self.get_active_courses()
                all_announcements = []

                for course in courses:
                    course_id = course.get("id")
                    course_name = course.get("name")

                    try:
                        endpoint = "/announcements"
                        params = {
                            "context_codes[]": f"course_{course_id}",
                            "latest_only": True,
                        }
                        announcements = self._call_api(endpoint, params)

                        for announcement in announcements[:3]:
                            all_announcements.append(
                                {
                                    "course": course_name,
                                    "title": announcement.get("title"),
                                    "message": announcement.get("message"),
                                    "posted_at": announcement.get("posted_at"),
                                    "html_url": announcement.get("html_url"),
                                }
                            )

                    except RequestException:
                        continue

                all_announcements.sort(
                    key=lambda x: x.get("posted_at", ""), reverse=True
                )
                return all_announcements[:limit]

        except RequestException as e:
            _logger.error("Failed to get announcements: %s", e)
            return []

    def get_assignment_submissions(
        self,
        course_id: int,
        assignment_id: int,
        include: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get submissions for an assignment.

        Args:
            course_id: Canvas course ID
            assignment_id: Assignment ID
            include: Optional data to include ['submission_comments', 'rubric_assessment',
                     'total_scores', 'user']

        Returns:
            List of submission objects
        """
        try:
            params = {}
            if include:
                for item in include:
                    params[f"include[]"] = item

            submissions = self._call_api(
                f"/courses/{course_id}/assignments/{assignment_id}/submissions", params
            )
            return submissions if isinstance(submissions, list) else []

        except RequestException as e:
            _logger.error(
                "Failed to get submissions for assignment %d: %s", assignment_id, e
            )
            return []

    def get_user_submission(
        self,
        course_id: int,
        assignment_id: int,
        user_id: int,
        include: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific user's submission for an assignment.

        Args:
            course_id: Canvas course ID
            assignment_id: Assignment ID
            user_id: User ID
            include: Optional data to include

        Returns:
            Submission object or None
        """
        try:
            params = {}
            if include:
                for item in include:
                    params[f"include[]"] = item

            submission = self._call_api(
                f"/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}",
                params,
            )
            return submission

        except RequestException as e:
            _logger.error("Failed to get user submission: %s", e)
            return None

    def get_assignment_overrides(
        self, course_id: int, assignment_id: int
    ) -> List[Dict[str, Any]]:
        """Get assignment overrides.

        Args:
            course_id: Canvas course ID
            assignment_id: Assignment ID

        Returns:
            List of override objects
        """
        try:
            overrides = self._call_api(
                f"/courses/{course_id}/assignments/{assignment_id}/overrides"
            )
            return overrides if isinstance(overrides, list) else []

        except RequestException as e:
            _logger.error("Failed to get assignment overrides: %s", e)
            return []

    def get_group_members(
        self, course_id: int, assignment_id: int, user_id: int
    ) -> List[Dict[str, Any]]:
        """Get group members for a group assignment.

        Args:
            course_id: Canvas course ID
            assignment_id: Assignment ID
            user_id: User ID

        Returns:
            List of group member objects
        """
        try:
            members = self._call_api(
                f"/courses/{course_id}/assignments/{assignment_id}/users/{user_id}/group_members"
            )
            return members if isinstance(members, list) else []

        except RequestException as e:
            _logger.error("Failed to get group members: %s", e)
            return []
