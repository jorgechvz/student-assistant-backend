"""Notion Integration Tools for LangChain agents.

Provides tools for creating, searching, and organizing content in Notion.
All content is formatted in clean Markdown which the NotionAPIAdapter
converts to proper Notion blocks (headings, lists, bold, code, tables, etc.).
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from langchain.tools import tool

_logger = logging.getLogger(__name__)


def create_notion_tools(notion_repo) -> list:
    """Create Notion tools for the LangChain agent.

    Args:
        notion_repo: NotionAPIAdapter instance (handles API calls + markdown→blocks)

    Returns:
        List of LangChain tools for Notion operations
    """

    @tool("get_notion_pages")
    def get_notion_pages() -> str:
        """List the top-level Notion pages the user has shared with the integration.

        **Call this FIRST before creating any page** so you know which
        parent page IDs are available.

        Use when the user asks:
        - "Show me my Notion pages"
        - "Where can I save notes in Notion?"

        Or internally before calling create_notion_page (to pick a parent_page_id).

        Returns:
            Numbered list of pages with their IDs and URLs.
        """
        try:
            pages = notion_repo.get_top_level_pages(max_results=20)

            if not pages:
                return (
                    "No Notion pages found. The user may need to share pages "
                    "with the integration from their Notion workspace."
                )

            lines = ["# Available Notion Pages\n"]
            for i, page in enumerate(pages, 1):
                title = page.get("title", "Untitled")
                page_id = page.get("id", "")
                url = page.get("url", "")
                edited = page.get("last_edited", "")
                lines.append(f"{i}. **{title}**")
                lines.append(f"   - ID: `{page_id}`")
                if edited:
                    lines.append(f"   - Last edited: {edited}")
                if url:
                    lines.append(f"   - [Open in Notion]({url})")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            _logger.error("get_notion_pages failed: %s", e)
            return f"❌ Failed to get Notion pages: {e}"

    @tool("get_notion_databases")
    def get_notion_databases() -> str:
        """List Notion databases shared with the integration.

        Use when the user asks:
        - "Show me my Notion databases"
        - "What databases do I have in Notion?"

        Returns:
            Numbered list of databases with their IDs and URLs.
        """
        try:
            databases = notion_repo.search_databases()

            if not databases:
                return (
                    "No Notion databases found. The user may need to create "
                    "a database or share it with the integration."
                )

            lines = ["# Available Notion Databases\n"]
            for i, db in enumerate(databases, 1):
                title = db.get("title", "Untitled")
                db_id = db.get("id", "")
                url = db.get("url", "")
                lines.append(f"{i}. **{title}**")
                lines.append(f"   - ID: `{db_id}`")
                if url:
                    lines.append(f"   - [Open in Notion]({url})")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            _logger.error("get_notion_databases failed: %s", e)
            return f"❌ Failed to get Notion databases: {e}"

    @tool("create_notion_page")
    def create_notion_page(
        title: str,
        content: str,
        parent_page_id: Optional[str] = None,
    ) -> str:
        """Create a new page in Notion with Markdown content.

        The content is automatically converted to Notion blocks (headings,
        bold, lists, code blocks, tables, etc.).

        **IMPORTANT — Before calling this tool:**
        1. Call get_notion_pages to get available parent page IDs.
        2. Ask the user WHERE they want the page created.
        3. Pass the chosen parent_page_id.

        Use when the user asks:
        - "Create a page in Notion called [title]"
        - "Save this to Notion"
        - "Make a Notion page with this content"

        Do NOT use for study notes, assignment trackers, or study plans
        — use the specific tools instead (create_study_notes,
        create_assignment_tracker, create_study_plan_page).

        Args:
            title: Page title.
            content: Page body in Markdown format. Supports:
                     # headings, **bold**, *italic*, - bullet lists,
                     1. numbered lists, - [ ] checklists, ```code blocks```,
                     [links](url), and tables.
            parent_page_id: Parent page ID (get from get_notion_pages).
                           If omitted, creates under the first available page.

        Returns:
            Confirmation with the Notion page URL.
        """
        try:
            result = notion_repo.create_page(
                title=title,
                content=content,
                parent_page_id=parent_page_id,
            )

            if result.get("error"):
                error = result["error"]
                if "parent" in error.lower() or not parent_page_id:
                    return (
                        f"❌ {error}\n\n"
                        f"💡 Use get_notion_pages to see available pages, "
                        f"then ask the user which page to use as the parent."
                    )
                return f"❌ Failed to create page: {error}"

            page_url = result.get("url", "")
            return f"✅ Notion page created!\n" f"**Title:** {title}\n" + (
                f"**URL:** {page_url}" if page_url else ""
            )

        except Exception as e:
            _logger.error("create_notion_page failed: %s", e)
            return f"❌ Failed to create Notion page: {e}"

    @tool("create_study_notes")
    def create_study_notes(
        course_name: str,
        topic: str,
        notes_content: str,
        parent_page_id: Optional[str] = None,
    ) -> str:
        """Create a well-formatted study notes page in Notion for a course topic.

        Generates a clean, organized page with metadata header and the provided
        notes content. The notes should be written in Markdown.

        **IMPORTANT — Before calling this tool:**
        1. Call get_notion_pages to find a parent page.
        2. Ask the user where to save the notes.

        Use when the user asks:
        - "Save my study notes for [course] on [topic] to Notion"
        - "Create notes in Notion for [topic]"
        - "Take notes for [course]"

        Args:
            course_name: Full course name (e.g., 'GS497.003 - Professional Projects').
            topic: Topic or lesson name (e.g., 'Week 3 - Networking Strategies').
            notes_content: Study notes in Markdown format. Use:
                          - # headings for sections
                          - **bold** for key terms
                          - - bullet lists for points
                          - 1. numbered lists for steps
                          - ```code``` for code snippets
            parent_page_id: Parent page ID (get from get_notion_pages).

        Returns:
            Confirmation with the Notion page URL.
        """
        try:
            title = f"📝 {course_name} — {topic}"
            today = datetime.now(timezone.utc).strftime("%B %d, %Y")

            content = (
                f"# {topic}\n\n"
                f"**Course:** {course_name}\n"
                f"**Date:** {today}\n\n"
                f"---\n\n"
                f"{notes_content}"
            )

            result = notion_repo.create_page(
                title=title,
                content=content,
                parent_page_id=parent_page_id,
            )

            if result.get("error"):
                return f"❌ Failed to create study notes: {result['error']}"

            page_url = result.get("url", "")
            return (
                f"Study notes saved to Notion!\n"
                f"**Course:** {course_name}\n"
                f"**Topic:** {topic}\n" + (f"**URL:** {page_url}" if page_url else "")
            )

        except Exception as e:
            _logger.error("create_study_notes failed: %s", e)
            return f"❌ Failed to create study notes: {e}"

    @tool("create_assignment_tracker")
    def create_assignment_tracker(
        course_name: str,
        assignment_name: str,
        due_date: str,
        points: Optional[str] = None,
        description: Optional[str] = None,
        parent_page_id: Optional[str] = None,
    ) -> str:
        """Create an assignment tracker page in Notion with a structured checklist.

        Generates a clean page with assignment metadata, description, a
        step-by-step checklist, and space for notes/resources.

        **IMPORTANT — Before calling this tool:**
        1. Call get_notion_pages to find a parent page.
        2. Ask the user where to save the tracker.

        Use when the user asks:
        - "Track [assignment] in Notion"
        - "Create an assignment tracker for [assignment]"
        - "Save this assignment to Notion with a checklist"

        Args:
            course_name: Course name (e.g., 'GS497.003 - Professional Projects').
            assignment_name: Assignment name (e.g., 'W03 Activity: Grow Your Network').
            due_date: Due date in YYYY-MM-DD format (e.g., '2026-02-14').
            points: Optional points possible (e.g., '25').
            description: Optional assignment description or instructions.
            parent_page_id: Parent page ID (get from get_notion_pages).

        Returns:
            Confirmation with the Notion page URL.
        """
        try:
            title = f"{assignment_name} — {course_name}"

            points_line = f"**Points:** {points}\n" if points else ""
            desc_section = f"## Description\n\n{description}\n\n" if description else ""

            content = (
                f"# {assignment_name}\n\n"
                f"**Course:** {course_name}\n"
                f"**Due Date:** {due_date}\n"
                f"{points_line}"
                f"**Status:** To Do\n\n"
                f"---\n\n"
                f"{desc_section}"
                f"## Progress Checklist\n\n"
                f"- [ ] Review assignment requirements\n"
                f"- [ ] Gather necessary materials / resources\n"
                f"- [ ] Complete first draft\n"
                f"- [ ] Review and revise\n"
                f"- [ ] Submit before deadline\n\n"
                f"## Notes\n\n"
                f"*Add your notes, links, and resources here.*\n"
            )

            result = notion_repo.create_page(
                title=title,
                content=content,
                parent_page_id=parent_page_id,
            )

            if result.get("error"):
                return f"❌ Failed to create assignment tracker: {result['error']}"

            page_url = result.get("url", "")
            return (
                f"Assignment tracker created in Notion!\n"
                f"**Assignment:** {assignment_name}\n"
                f"**Course:** {course_name}\n"
                f"**Due:** {due_date}\n" + (f"**URL:** {page_url}" if page_url else "")
            )

        except Exception as e:
            _logger.error("create_assignment_tracker failed: %s", e)
            return f"❌ Failed to create assignment tracker: {e}"

    @tool("create_study_plan_page")
    def create_study_plan_page(
        title: str,
        goals: str,
        schedule: str,
        parent_page_id: Optional[str] = None,
    ) -> str:
        """Create a study plan page in Notion with goals, schedule, and progress tracking.

        **IMPORTANT — Before calling this tool:**
        1. Call get_notion_pages to find a parent page.
        2. Ask the user where to save the plan.

        Use when the user asks:
        - "Save this study plan to Notion"
        - "Create a study plan page in Notion"
        - "Put my weekly plan in Notion"

        Do NOT confuse with create_weekly_study_plan (Canvas tool that generates
        a plan) — this tool SAVES a plan to Notion.

        Args:
            title: Study plan title (e.g., 'Week 6 Study Plan — Feb 12-18').
            goals: Study goals in Markdown format. Example:
                   "- Complete W03 Activity: Grow Your Network\\n- Review for quiz"
            schedule: Schedule details in Markdown format. Example:
                      "## Monday\\n- 2:00 PM: Study networking (1.5h)\\n## Tuesday\\n..."
            parent_page_id: Parent page ID (get from get_notion_pages).

        Returns:
            Confirmation with the Notion page URL.
        """
        try:
            today = datetime.now(timezone.utc).strftime("%B %d, %Y")

            content = (
                f"# {title}\n\n"
                f"**Created:** {today}\n\n"
                f"---\n\n"
                f"## Goals\n\n"
                f"{goals}\n\n"
                f"## Schedule\n\n"
                f"{schedule}\n\n"
                f"## Progress\n\n"
                f"- [ ] Week goals reviewed\n"
                f"- [ ] All study sessions completed\n"
                f"- [ ] Assignments submitted on time\n\n"
                f"## Notes & Reflections\n\n"
                f"*Add reflections at the end of the week.*\n"
            )

            result = notion_repo.create_page(
                title=f"{title}",
                content=content,
                parent_page_id=parent_page_id,
            )

            if result.get("error"):
                return f"❌ Failed to create study plan: {result['error']}"

            page_url = result.get("url", "")
            return f"Study plan saved to Notion!\n" f"**Title:** {title}\n" + (
                f"**URL:** {page_url}" if page_url else ""
            )

        except Exception as e:
            _logger.error("create_study_plan_page failed: %s", e)
            return f"❌ Failed to create study plan: {e}"

    @tool("search_notion")
    def search_notion(query: str) -> str:
        """Search for pages AND databases in the user's Notion workspace by keyword.

        Use when the user asks:
        - "Find my notes about [topic] in Notion"
        - "Search Notion for [keyword]"
        - "Do I have a page about [topic]?"
        - "Is there anything in Notion about [subject]?"

        Args:
            query: Search text (matches page titles and content).

        Returns:
            List of matching pages and databases with URLs.
        """
        try:
            # Use the Notion search API directly (searches titles + content)
            matching_pages = notion_repo.search_pages(query, max_results=20)

            # Also search databases
            databases = notion_repo.search_databases(query)

            if not matching_pages and not databases:
                return f"No results found for '{query}' in Notion."

            lines = [f"# Notion Search Results: '{query}'\n"]

            if matching_pages:
                lines.append("## Pages\n")
                for p in matching_pages:
                    title = p.get("title", "Untitled")
                    url = p.get("url", "")
                    edited = p.get("last_edited", "")
                    lines.append(f"- **{title}**")
                    if edited:
                        lines.append(f"  Last edited: {edited}")
                    if url:
                        lines.append(f"  [Open in Notion]({url})")
                    lines.append("")

            if databases:
                lines.append("## Databases\n")
                for db in databases:
                    title = db.get("title", "Untitled")
                    url = db.get("url", "")
                    lines.append(f"- **{title}**")
                    if url:
                        lines.append(f"  [Open in Notion]({url})")
                    lines.append("")

            return "\n".join(lines)

        except Exception as e:
            _logger.error("search_notion failed: %s", e)
            return f"❌ Failed to search Notion: {e}"

    return [
        get_notion_pages,
        get_notion_databases,
        create_notion_page,
        create_study_notes,
        create_assignment_tracker,
        create_study_plan_page,
        search_notion,
    ]
