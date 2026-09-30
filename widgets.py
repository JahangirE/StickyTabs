"""
Custom Qt widgets and shared UI color definitions for StickyTabs.

This module contains:
- Shared color palettes used by the application's tab, note, and text controls.
- ColoredTabBar: a QTabBar subclass that supports per-tab colors.
- LinkTextEdit: a QTextEdit subclass with clickable hyperlink support.
"""

import re

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QIcon,
    QPixmap,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QStyle,
    QStyleOptionTab,
    QStylePainter,
    QTabBar,
    QTextEdit,
)


# Tab headings: stronger pastel shades
TAB_COLORS = {
    "None": None,
    "Yellow": "#FFF3B0",
    "Blue": "#BDE0FE",
    "Green": "#CAFFBF",
    "Red": "#FFADAD",
    "Purple": "#D0BFFF",
    "Gray": "#E5E5E5",
}


# Note backgrounds: lighter versions of the tab colors
NOTE_COLORS = {
    "None": None,
    "Yellow": "#FFF9D6",
    "Blue": "#E3F2FD",
    "Green": "#E8FFE2",
    "Red": "#FFE0E0",
    "Purple": "#EEE6FF",
    "Gray": "#F3F3F3",
}


# Text colors: darker for readability
TEXT_COLORS = {
    "Black": "#000000",
    "Red": "#C62828",
    "Blue": "#1565C0",
    "Green": "#2E7D32",
    "Purple": "#6A1B9A",
    "Gray": "#616161",
}


# Standard hyperlink color used by LinkTextEdit
LINK_COLOR = "#0000FF"


def make_color_icon(color_code, size=12):
    """Create a small square color swatch for menus and dropdowns."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(color_code))
    return QIcon(pixmap)


class ColoredTabBar(QTabBar):
    """Tab bar that paints each tab using its stored pastel color."""

    def paintEvent(self, event):
        """Draw each tab using its stored color while preserving Qt's native shape."""
        painter = QStylePainter(self)

        for index in range(self.count()):
            option = QStyleOptionTab()
            self.initStyleOption(option, index)

            # Draw Qt's normal tab shape so native borders remain intact.
            painter.drawControl(
                QStyle.ControlElement.CE_TabBarTabShape,
                option,
            )

            color_name = self.tabData(index) or "None"
            color_code = TAB_COLORS.get(color_name)

            if color_code:
                # Leave a small margin so the native tab border remains visible.
                tab_area = option.rect.adjusted(2, 2, -2, -1)
                painter.fillRect(tab_area, QColor(color_code))

            painter.drawControl(
                QStyle.ControlElement.CE_TabBarTabLabel,
                option,
            )


class LinkTextEdit(QTextEdit):
    """Text editor that preserves hyperlinks and opens them with Ctrl+click."""

    URL_PATTERN = re.compile(r"https?://[^\s]+")

    def mousePressEvent(self, event):
        """Open a hyperlink when the user Ctrl+clicks it."""

        ctrl_pressed = bool(
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
        )

        if ctrl_pressed:
            link = self.anchorAt(event.position().toPoint())

            if link:
                QDesktopServices.openUrl(QUrl(link))
                return

        super().mousePressEvent(event)

    def insertFromMimeData(self, source):
        """
        Preserve rich clipboard content while giving hyperlinks
        a consistent blue, underlined appearance.
        """

        pasted_text = source.text()

        if source.hasHtml():
            start_position = self.textCursor().position()

            super().insertFromMimeData(source)

            end_position = self.textCursor().position()

            self._normalize_link_style(
                start_position,
                end_position,
            )
            return

        match = self.URL_PATTERN.fullmatch(pasted_text.strip())

        if match:
            url = match.group()

            link_format = QTextCharFormat()
            link_format.setAnchor(True)
            link_format.setAnchorHref(url)
            link_format.setForeground(QColor(LINK_COLOR))
            link_format.setFontUnderline(True)

            self.textCursor().insertText(url, link_format)
            return

        super().insertFromMimeData(source)

    def _normalize_link_style(self, start_position, end_position):
        """Make hyperlinks in newly pasted rich text blue and underlined."""

        document = self.document()

        # Inspect only the newly pasted range and restyle characters
        # that belong to hyperlinks.
        for position in range(start_position, end_position):
            cursor = QTextCursor(document)
            cursor.setPosition(position)
            cursor.setPosition(
                position + 1,
                QTextCursor.MoveMode.KeepAnchor,
            )

            fmt = cursor.charFormat()

            if fmt.isAnchor():
                fmt.setForeground(QColor(LINK_COLOR))
                fmt.setFontUnderline(True)
                cursor.mergeCharFormat(fmt)
