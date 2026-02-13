"""Notion API Adapter for LangChain tools."""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests
from mistletoe import Document
from mistletoe.block_token import (
    Heading,
    Paragraph,
    List as MList,
    ListItem,
    CodeFence,
    Table,
    TableRow,
    TableCell,
    ThematicBreak,
)
from mistletoe.span_token import RawText, Strong, Emphasis, Link, InlineCode

from requests.exceptions import RequestException

_logger = logging.getLogger(__name__)


class NotionAPIAdapter:
    """Adapter for Notion API operations."""

    def __init__(self, access_token: str):
        """Initialize Notion API adapter.

        Args:
            access_token: Notion integration access token
        """
        self.access_token = access_token
        self.base_url = "https://api.notion.com/v1"
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            }
        )

    def _call_api(
        self,
        endpoint: str,
        method: str = "GET",
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make a Notion API request.

        Args:
            endpoint: API endpoint (e.g., '/pages')
            method: HTTP method
            json_data: Request body for POST/PATCH
            params: Query parameters

        Returns:
            JSON response data
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = self._session.get(url, params=params, timeout=30)
            elif method == "POST":
                response = self._session.post(url, json=json_data, timeout=30)
            elif method == "PATCH":
                response = self._session.patch(url, json=json_data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except RequestException as e:
            _logger.error("Notion API error: %s", str(e))
            raise

    def create_page(
        self,
        title: str,
        content: str,
        parent_database_id: Optional[str] = None,
        parent_page_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new page in Notion.

        Args:
            title: Page title
            content: Page content (plain text or markdown)
            parent_database_id: Optional database to create page in
            parent_page_id: Optional parent page (if not using database)

        Note:
            If neither parent_database_id nor parent_page_id is provided,
            the page will be created at the workspace root level (requires
            workspace integration permissions).

        Returns:
            Created page data with URL
        """
        try:
            if parent_database_id:
                parent = {"database_id": parent_database_id}
            elif parent_page_id:
                parent = {"page_id": parent_page_id}
            else:
                pages = self.get_top_level_pages()
                if pages:
                    parent = {"page_id": pages[0]["id"]}
                else:
                    return {
                        "error": "No parent specified and no accessible pages found. Please specify a parent_page_id or parent_database_id.",
                        "suggestion": "Use get_pages tool to see available pages, or create a database first.",
                    }

            properties = {"title": {"title": [{"text": {"content": title}}]}}

            children = self._parse_content_to_blocks(content)

            payload = {
                "parent": parent,
                "properties": properties,
                "children": children[:100],
            }

            response = self._call_api("/pages", method="POST", json_data=payload)

            if len(children) > 100:
                page_id = response.get("id")
                for i in range(100, len(children), 100):
                    batch = children[i : i + 100]
                    self._call_api(
                        f"/blocks/{page_id}/children",
                        method="PATCH",
                        json_data={"children": batch},
                    )

            return {
                "id": response.get("id"),
                "url": response.get("url"),
                "created_time": response.get("created_time"),
            }

        except RequestException as e:
            error_msg = str(e)
            _logger.error("Failed to create Notion page: %s", error_msg)

            if "parent" in error_msg.lower():
                return {
                    "error": "Could not create page without a parent. Use get_pages to find available pages or specify a parent_page_id.",
                }

            return {"error": error_msg}

    def get_top_level_pages(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """Get top-level pages accessible to the integration.

        Only returns pages whose parent is the workspace itself,
        NOT child or grandchild pages.

        Args:
            max_results: Maximum number of pages to return

        Returns:
            List of top-level pages with id, title, and url
        """
        try:
            payload = {
                "filter": {"property": "object", "value": "page"},
                "page_size": 100,
                "sort": {"timestamp": "last_edited_time", "direction": "descending"},
            }

            response = self._call_api("/search", method="POST", json_data=payload)

            results = []
            for page in response.get("results", []):
                parent = page.get("parent", {})
                if parent.get("type") != "workspace":
                    continue

                properties = page.get("properties", {})
                title = "Untitled"

                for _, prop_value in properties.items():
                    if prop_value.get("type") == "title":
                        title_array = prop_value.get("title", [])
                        if title_array:
                            title = "".join(
                                t.get("plain_text", "") for t in title_array
                            )
                        break

                results.append(
                    {
                        "id": page.get("id"),
                        "title": title,
                        "url": page.get("url"),
                        "last_edited": page.get("last_edited_time"),
                    }
                )

                if len(results) >= max_results:
                    break

            return results

        except RequestException as e:
            _logger.error("Failed to get top-level pages: %s", e)
            return []

    def search_pages(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Search for pages in the Notion workspace by keyword.

        Args:
            query: Search text (matches page titles and content)
            max_results: Maximum number of results to return

        Returns:
            List of matching pages with id, title, url
        """
        try:
            payload = {
                "query": query,
                "filter": {"property": "object", "value": "page"},
                "page_size": min(max_results, 100),
                "sort": {"timestamp": "last_edited_time", "direction": "descending"},
            }

            response = self._call_api("/search", method="POST", json_data=payload)

            results = []
            for page in response.get("results", []):
                properties = page.get("properties", {})
                title = "Untitled"

                for _, prop_value in properties.items():
                    if prop_value.get("type") == "title":
                        title_array = prop_value.get("title", [])
                        if title_array:
                            title = "".join(
                                t.get("plain_text", "") for t in title_array
                            )
                        break

                results.append(
                    {
                        "id": page.get("id"),
                        "title": title,
                        "url": page.get("url"),
                        "last_edited": page.get("last_edited_time"),
                    }
                )

            return results

        except RequestException as e:
            _logger.error("Failed to search pages: %s", e)
            return []

    def search_databases(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for databases in Notion workspace.

        Args:
            query: Optional search query to filter databases

        Returns:
            List of matching databases
        """
        try:
            payload = {
                "filter": {"property": "object", "value": "database"},
                "page_size": 100,
            }

            if query:
                payload["query"] = query

            response = self._call_api("/search", method="POST", json_data=payload)

            databases = []
            for db in response.get("results", []):
                title_array = db.get("title", [])
                title = "".join(t.get("plain_text", "") for t in title_array)

                databases.append(
                    {
                        "id": db.get("id"),
                        "title": title,
                        "url": db.get("url"),
                    }
                )

            return databases

        except RequestException as e:
            _logger.error("Failed to search databases: %s", e)
            return []

    @staticmethod
    def get_current_date() -> str:
        """Get current date in readable format.

        Returns:
            Current date string
        """
        return datetime.utcnow().strftime("%Y-%m-%d")

    def _parse_content_to_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Parse Markdown to Notion blocks using mistletoe."""
        try:
            doc = Document(content)
            blocks = []

            for child in doc.children:
                notion_blocks = self._convert_mistletoe_to_notion(child)
                if notion_blocks:
                    if isinstance(notion_blocks, list):
                        blocks.extend(notion_blocks)
                    else:
                        blocks.append(notion_blocks)

            return blocks[:100]

        except (ValueError, TypeError, AttributeError, Exception) as e:
            _logger.warning(
                "Mistletoe parsing failed (%s). Falling back to simple parser.", str(e)
            )
            return self._simple_markdown_parse(content)

    def _convert_mistletoe_to_notion(self, token) -> Optional[Any]:
        """Convert mistletoe token to Notion block(s)."""

        if isinstance(token, ThematicBreak):
            return {
                "object": "block",
                "type": "divider",
                "divider": {},
            }

        if isinstance(token, Heading):
            level = min(token.level, 3)
            heading_type = f"heading_{level}"
            rich_text = self._extract_rich_text(token.children)

            return {
                "object": "block",
                "type": heading_type,
                heading_type: {"rich_text": rich_text},
            }

        elif isinstance(token, Paragraph):
            rich_text = self._extract_rich_text(token.children)

            if not rich_text or (
                len(rich_text) == 1 and not rich_text[0]["text"]["content"].strip()
            ):
                return None

            return {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": rich_text},
            }

        elif isinstance(token, MList):
            list_blocks = []
            is_ordered = hasattr(token, "start") and token.start is not None
            list_type = "numbered_list_item" if is_ordered else "bulleted_list_item"

            for item in token.children:
                if isinstance(item, ListItem):
                    rich_text = []

                    for child in item.children:
                        if isinstance(child, Paragraph):
                            rich_text.extend(self._extract_rich_text(child.children))
                        else:
                            rich_text.extend(self._extract_rich_text([child]))

                    if not rich_text or not any(
                        rt["text"]["content"].strip() for rt in rich_text
                    ):
                        continue

                    full_text = "".join(rt["text"]["content"] for rt in rich_text)
                    checkbox_match = re.match(r"^\[([ xX])\]\s*(.*)", full_text)

                    if checkbox_match:
                        checked = checkbox_match.group(1).lower() == "x"
                        todo_text = checkbox_match.group(2)
                        todo_rich_text = self._parse_inline_markdown(todo_text)
                        list_blocks.append(
                            {
                                "object": "block",
                                "type": "to_do",
                                "to_do": {
                                    "rich_text": todo_rich_text,
                                    "checked": checked,
                                },
                            }
                        )
                    else:
                        list_blocks.append(
                            {
                                "object": "block",
                                "type": list_type,
                                list_type: {"rich_text": rich_text},
                            }
                        )

            return list_blocks if list_blocks else None

        elif isinstance(token, CodeFence):
            code_content = ""
            if token.children and hasattr(token.children[0], "content"):
                code_content = token.children[0].content

            return {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": code_content}}],
                    "language": token.language or "plain text",
                },
            }

        elif isinstance(token, Table):
            all_rows: List[List[str]] = []

            if hasattr(token, "header") and token.header:
                header_cells = []
                if hasattr(token.header, "children") and token.header.children:
                    for cell in token.header.children:
                        if isinstance(cell, TableCell):
                            header_cells.append(self._extract_text_only(cell.children))
                if header_cells:
                    all_rows.append(header_cells)

            for row in token.children:
                if isinstance(row, TableRow):
                    cells = []
                    for cell in row.children:
                        if isinstance(cell, TableCell):
                            cells.append(self._extract_text_only(cell.children))
                    if cells:
                        all_rows.append(cells)

            if not all_rows:
                return None

            num_cols = max(len(r) for r in all_rows)
            for r in all_rows:
                while len(r) < num_cols:
                    r.append("")

            table_rows = []
            for row_data in all_rows:
                table_rows.append(
                    {
                        "type": "table_row",
                        "table_row": {
                            "cells": [
                                [
                                    {
                                        "type": "text",
                                        "text": {"content": cell_text},
                                    }
                                ]
                                for cell_text in row_data
                            ]
                        },
                    }
                )

            return {
                "object": "block",
                "type": "table",
                "table": {
                    "table_width": num_cols,
                    "has_column_header": bool(
                        hasattr(token, "header") and token.header
                    ),
                    "has_row_header": False,
                    "children": table_rows,
                },
            }

        return None

    def _parse_inline_markdown(self, text: str) -> List[Dict[str, Any]]:
        """Parse inline markdown (bold, italic, code, links) into Notion rich_text."""
        rich_text = []
        pattern = re.compile(
            r"(\*\*(.+?)\*\*" r"|\*(.+?)\*" r"|`(.+?)`" r"|\[(.+?)\]\((.+?)\)" r")"
        )
        last_end = 0
        for m in pattern.finditer(text):
            if m.start() > last_end:
                plain = text[last_end : m.start()]
                if plain:
                    rich_text.append({"type": "text", "text": {"content": plain}})
            if m.group(2):
                rich_text.append(
                    {
                        "type": "text",
                        "text": {"content": m.group(2)},
                        "annotations": {"bold": True},
                    }
                )
            elif m.group(3):
                rich_text.append(
                    {
                        "type": "text",
                        "text": {"content": m.group(3)},
                        "annotations": {"italic": True},
                    }
                )
            elif m.group(4):
                rich_text.append(
                    {
                        "type": "text",
                        "text": {"content": m.group(4)},
                        "annotations": {"code": True},
                    }
                )
            elif m.group(5):
                rich_text.append(
                    {
                        "type": "text",
                        "text": {
                            "content": m.group(5),
                            "link": {"url": m.group(6)},
                        },
                    }
                )
            last_end = m.end()

        if last_end < len(text):
            remaining = text[last_end:]
            if remaining:
                rich_text.append({"type": "text", "text": {"content": remaining}})

        return rich_text if rich_text else [{"type": "text", "text": {"content": text}}]

    def _extract_rich_text(self, tokens) -> List[Dict[str, Any]]:
        """Extract rich text from mistletoe tokens with proper formatting."""
        rich_text = []

        for token in tokens:
            if isinstance(token, RawText):
                if token.content:
                    rich_text.append(
                        {"type": "text", "text": {"content": token.content}}
                    )

            elif isinstance(token, Strong):
                content = self._extract_text_only(token.children)
                if content:
                    rich_text.append(
                        {
                            "type": "text",
                            "text": {"content": content},
                            "annotations": {"bold": True},
                        }
                    )

            elif isinstance(token, Emphasis):
                content = self._extract_text_only(token.children)
                if content:
                    rich_text.append(
                        {
                            "type": "text",
                            "text": {"content": content},
                            "annotations": {"italic": True},
                        }
                    )

            elif isinstance(token, Link):
                content = self._extract_text_only(token.children)
                if content:
                    rich_text.append(
                        {
                            "type": "text",
                            "text": {"content": content, "link": {"url": token.target}},
                        }
                    )

            elif isinstance(token, InlineCode):
                if token.children and hasattr(token.children[0], "content"):
                    rich_text.append(
                        {
                            "type": "text",
                            "text": {"content": token.children[0].content},
                            "annotations": {"code": True},
                        }
                    )

            elif isinstance(token, Paragraph):
                rich_text.extend(self._extract_rich_text(token.children))

            elif hasattr(token, "children"):
                rich_text.extend(self._extract_rich_text(token.children))

        return rich_text if rich_text else [{"type": "text", "text": {"content": ""}}]

    def _extract_text_only(self, tokens) -> str:
        """Extract plain text content from tokens recursively."""
        text_parts = []

        for token in tokens:
            if isinstance(token, RawText):
                text_parts.append(token.content)
            elif isinstance(token, str):
                text_parts.append(token)
            elif hasattr(token, "children"):
                text_parts.append(self._extract_text_only(token.children))
            elif hasattr(token, "content"):
                text_parts.append(token.content)

        return "".join(text_parts)

    def _simple_markdown_parse(self, content: str) -> List[Dict[str, Any]]:
        """Fallback simple markdown parser.

        Handles: headings (h1-h3), dividers (---), bullet lists, numbered lists,
        checkboxes (- [ ] / - [x]), bold/italic inline, and pipe-delimited tables.
        """
        blocks = []
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()

            if not line:
                i += 1
                continue

            if re.match(r"^-{3,}$", line.strip()):
                blocks.append({"object": "block", "type": "divider", "divider": {}})
                i += 1
                continue

            heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)
            if heading_match:
                level = min(len(heading_match.group(1)), 3)
                heading_type = f"heading_{level}"
                heading_text = heading_match.group(2)
                blocks.append(
                    {
                        "object": "block",
                        "type": heading_type,
                        heading_type: {
                            "rich_text": self._parse_inline_markdown(heading_text)
                        },
                    }
                )
                i += 1
                continue

            checkbox_match = re.match(r"^-\s+\[([ xX])\]\s+(.*)", line)
            if checkbox_match:
                checked = checkbox_match.group(1).lower() == "x"
                todo_text = checkbox_match.group(2)
                blocks.append(
                    {
                        "object": "block",
                        "type": "to_do",
                        "to_do": {
                            "rich_text": self._parse_inline_markdown(todo_text),
                            "checked": checked,
                        },
                    }
                )
                i += 1
                continue

            bullet_match = re.match(r"^[-*]\s+(.+)$", line)
            if bullet_match:
                item_text = bullet_match.group(1)
                blocks.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": self._parse_inline_markdown(item_text)
                        },
                    }
                )
                i += 1
                continue

            num_match = re.match(r"^\d+\.\s+(.+)$", line)
            if num_match:
                item_text = num_match.group(1)
                blocks.append(
                    {
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": self._parse_inline_markdown(item_text)
                        },
                    }
                )
                i += 1
                continue

            if line.strip().startswith("|") and "|" in line[1:]:
                table_rows_raw: List[List[str]] = []
                while i < len(lines):
                    tline = lines[i].rstrip()
                    if not tline.strip().startswith("|"):
                        break
                    if re.match(r"^\|[\s\-:|]+\|$", tline.strip()):
                        i += 1
                        continue
                    cells = [c.strip() for c in tline.strip().strip("|").split("|")]
                    table_rows_raw.append(cells)
                    i += 1

                if table_rows_raw:
                    num_cols = max(len(r) for r in table_rows_raw)
                    for r in table_rows_raw:
                        while len(r) < num_cols:
                            r.append("")

                    notion_rows = []
                    for row_data in table_rows_raw:
                        notion_rows.append(
                            {
                                "type": "table_row",
                                "table_row": {
                                    "cells": [
                                        [
                                            {
                                                "type": "text",
                                                "text": {"content": c},
                                            }
                                        ]
                                        for c in row_data
                                    ]
                                },
                            }
                        )

                    blocks.append(
                        {
                            "object": "block",
                            "type": "table",
                            "table": {
                                "table_width": num_cols,
                                "has_column_header": len(notion_rows) > 1,
                                "has_row_header": False,
                                "children": notion_rows,
                            },
                        }
                    )
                continue

            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": self._parse_inline_markdown(line)},
                }
            )

            i += 1

        return blocks
