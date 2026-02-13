"""HTML to Markdown converter module."""

import re
from html.parser import HTMLParser


class HTMLToMarkdownConverter(HTMLParser):
    """Convert HTML to Markdown."""

    def __init__(self):
        super().__init__()
        self.markdown = []
        self.current_tag = None
        self.list_level = 0

    def handle_starttag(self, tag, attrs):
        if tag == "h1":
            self.current_tag = "# "
        elif tag == "h2":
            self.current_tag = "## "
        elif tag == "h3":
            self.current_tag = "### "
        elif tag == "h4":
            self.current_tag = "#### "
        elif tag == "strong" or tag == "b":
            self.current_tag = "**"
        elif tag == "em" or tag == "i":
            self.current_tag = "_"
        elif tag == "ul":
            self.list_level += 1
        elif tag == "ol":
            self.list_level += 1
        elif tag == "li":
            self.current_tag = "- " if self.list_level > 0 else ""
        elif tag == "p":
            self.current_tag = ""
        elif tag == "br":
            self.markdown.append("\n")

    def handle_endtag(self, tag):
        if tag in ["strong", "b"]:
            self.markdown.append("**")
            self.current_tag = None
        elif tag in ["em", "i"]:
            self.markdown.append("_")
            self.current_tag = None
        elif tag in ["h1", "h2", "h3", "h4"]:
            self.markdown.append("\n\n")
            self.current_tag = None
        elif tag == "p":
            self.markdown.append("\n\n")
            self.current_tag = None
        elif tag == "li":
            self.markdown.append("\n")
            self.current_tag = None
        elif tag in ["ul", "ol"]:
            self.list_level -= 1
            self.markdown.append("\n")

    def handle_data(self, data):
        if data.strip():
            if self.current_tag:
                self.markdown.append(self.current_tag)
                self.current_tag = None
            self.markdown.append(data.strip())

    def get_markdown(self):  # pylint: disable=missing-function-docstring
        result = "".join(self.markdown)
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()
