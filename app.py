"""Main application window and user-interface behavior for StickyTabs."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QTextCharFormat,
    QTextCursor,
    QTextListFormat,
)
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from storage import load_data, save_data
from widgets import (
    ColoredTabBar,
    LinkTextEdit,
    NOTE_COLORS,
    TAB_COLORS,
    TEXT_COLORS,
    make_color_icon,
)

MAX_TABS = 10
AUTOSAVE_INTERVAL_MS = 5000
DEFAULT_FONT_SIZE = 11


class StickyTabsApp(QMainWindow):
    """Main application window for StickyTabs."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("StickyTabs")
        self.resize(800, 600)

        self._build_ui()
        self._connect_signals()

        self.load_notes()
        
        # Prevent repeated error dialogs during consecutive autosave failures.
        self.save_error_shown = False

        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.save_notes)
        self.autosave_timer.start(AUTOSAVE_INTERVAL_MS)

    
    def _build_ui(self):
        """Create the main window layout and application controls."""

        # Main container
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.setTabBar(ColoredTabBar())
        self.tabs.setMovable(True)

        main_layout.addWidget(self.tabs)

        # Shared button styling
        button_style = """
            QPushButton {
                border: 1px solid #c8c8c8;
                border-radius: 3px;
                background-color: white;
                padding: 4px 4px;
            }

            QPushButton:checked {
                background-color: #d0d0d0;
            }
        """

        # Top tab controls
        self.add_tab_button = QPushButton("＋")
        self.add_tab_button.setToolTip("Add new tab")

        add_tab_font = self.add_tab_button.font()
        add_tab_font.setPointSize(14)
        self.add_tab_button.setFont(add_tab_font)
        self.add_tab_button.setStyleSheet(button_style)

        self.tab_options_button = QPushButton("Tab Options")
        self.tab_options_button.setToolTip("Manage current tab")
        self.tab_options_button.setStyleSheet(button_style)

        self.tab_menu = QMenu(self)
        self.tab_options_button.setMenu(self.tab_menu)

        tab_controls = QWidget()
        tab_controls_layout = QHBoxLayout()
        tab_controls_layout.setContentsMargins(0, 0, 0, 0)
        tab_controls_layout.setSpacing(4)

        tab_controls_layout.addWidget(self.add_tab_button)
        tab_controls_layout.addWidget(self.tab_options_button)

        tab_controls.setLayout(tab_controls_layout)

        self.tabs.setCornerWidget(
            tab_controls,
            Qt.Corner.TopRightCorner,
        )

        # Bottom formatting controls
        bottom_toolbar = QWidget()
        bottom_toolbar_layout = QHBoxLayout()

        self.bold_button = QPushButton("B")
        self.bold_button.setCheckable(True)
        bold_font = self.bold_button.font()
        bold_font.setBold(True)
        self.bold_button.setFont(bold_font)
        self.bold_button.setStyleSheet(button_style)

        self.italic_button = QPushButton("I")
        self.italic_button.setCheckable(True)
        italic_font = self.italic_button.font()
        italic_font.setItalic(True)
        self.italic_button.setFont(italic_font)
        self.italic_button.setStyleSheet(button_style)

        self.underline_button = QPushButton("U")
        self.underline_button.setCheckable(True)
        underline_font = self.underline_button.font()
        underline_font.setUnderline(True)
        self.underline_button.setFont(underline_font)
        self.underline_button.setStyleSheet(button_style)

        self.strike_button = QPushButton("S")
        self.strike_button.setCheckable(True)
        strike_font = self.strike_button.font()
        strike_font.setStrikeOut(True)
        self.strike_button.setFont(strike_font)
        self.strike_button.setStyleSheet(button_style)

        self.outdent_button = QPushButton("⇤")
        self.outdent_button.setToolTip("Decrease indent")
        self.outdent_button.setStyleSheet(button_style)

        self.indent_button = QPushButton("⇥")
        self.indent_button.setToolTip("Increase indent")
        self.indent_button.setStyleSheet(button_style)

        self.style_dropdown = QComboBox()
        self.style_dropdown.addItems(
            ["Text Style", "Title", "Heading", "Subheading", "Body"]
        )

        self.color_dropdown = QComboBox()
        self.color_dropdown.addItem("Text Color")

        for color_name, color_code in TEXT_COLORS.items():
            self.color_dropdown.addItem(
                make_color_icon(color_code),
                color_name,
            )

        self.list_dropdown = QComboBox()
        self.list_dropdown.addItem("Lists & Bullets", None)
        self.list_dropdown.addItem("●  ───", "Circle")
        self.list_dropdown.addItem("■  ───", "Square")
        self.list_dropdown.addItem("1.  ───", "Numbered")

        self.clear_button = QPushButton("Clear Tab")
        self.clear_button.setToolTip("Clear current tab")
        self.clear_button.setStyleSheet(button_style)

        bottom_toolbar_layout.addWidget(self.bold_button)
        bottom_toolbar_layout.addWidget(self.italic_button)
        bottom_toolbar_layout.addWidget(self.underline_button)
        bottom_toolbar_layout.addWidget(self.strike_button)

        bottom_toolbar_layout.addWidget(self.outdent_button)
        bottom_toolbar_layout.addWidget(self.indent_button)

        bottom_toolbar_layout.addWidget(self.style_dropdown)
        bottom_toolbar_layout.addWidget(self.color_dropdown)
        bottom_toolbar_layout.addWidget(self.list_dropdown)
        bottom_toolbar_layout.addWidget(self.clear_button)

        bottom_toolbar.setLayout(bottom_toolbar_layout)
        main_layout.addWidget(bottom_toolbar)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)


    def _connect_signals(self):
        """Connect interface controls to their application behavior."""

        # Tab controls
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.tabs.tabBarDoubleClicked.connect(self.rename_tab)
        self.tab_menu.aboutToShow.connect(self.rebuild_tab_menu)

        # Text formatting
        self.bold_button.clicked.connect(self.toggle_bold)
        self.italic_button.clicked.connect(self.toggle_italic)
        self.underline_button.clicked.connect(self.toggle_underline)
        self.strike_button.clicked.connect(self.toggle_strike)

        # Paragraph formatting
        self.indent_button.clicked.connect(self.indent_forward)
        self.outdent_button.clicked.connect(self.indent_backward)

        # Dropdown controls
        self.style_dropdown.currentTextChanged.connect(
            self.apply_text_style
        )
        self.color_dropdown.currentTextChanged.connect(
            self.apply_text_color
        )
        self.list_dropdown.currentIndexChanged.connect(
            self.apply_list_style
        )

        self.clear_button.clicked.connect(self.clear_current_tab)



    # Helper Methods
    def create_note_tab(self, name, content="", color_name="None"):
        """Create a note tab and return its tab index."""

        editor = LinkTextEdit()

        font = editor.font()
        font.setPointSize(DEFAULT_FONT_SIZE)
        editor.setFont(font)

        editor.setHtml(content)

        tab_index = self.tabs.addTab(editor, name)
        self.tabs.tabBar().setTabData(tab_index, color_name)

        self.apply_note_background(tab_index)

        return tab_index


    def get_current_editor(self):
        """Return the text editor in the currently selected tab."""

        return self.tabs.currentWidget()


    def get_next_note_name(self):
        """Return the first unused default note name."""

        existing_names = {
            self.tabs.tabText(index)
            for index in range(self.tabs.count())
        }

        number = 1

        while f"Note {number}" in existing_names:
            number += 1

        return f"Note {number}"


    def apply_note_background(self, tab_index):
        """Apply the tab's selected pastel color to its note background."""

        if tab_index < 0:
            return

        editor = self.tabs.widget(tab_index)

        color_name = self.tabs.tabBar().tabData(tab_index) or "None"
        color_code = NOTE_COLORS.get(color_name)

        if color_code:
            editor.setStyleSheet(
                f"QTextEdit {{ background-color: {color_code}; }}"
            )
        else:
            editor.setStyleSheet("")


    def adjust_indent(self, amount):
        """Increase or decrease indentation for the selected paragraph(s)."""

        editor = self.get_current_editor()
        cursor = editor.textCursor()
        document = editor.document()

        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd() - 1
        else:
            start = cursor.position()
            end = cursor.position()

        block = document.findBlock(start)
        last_block = document.findBlock(end)

        while block.isValid():
            block_cursor = QTextCursor(block)
            block_format = block.blockFormat()

            new_indent = max(
                0,
                block_format.indent() + amount,
            )

            block_format.setIndent(new_indent)
            block_cursor.setBlockFormat(block_format)

            if block == last_block:
                break

            block = block.next()

        editor.setFocus()



    # Tab Management Methods
    def add_new_tab(self):
        """Create a new note tab and switch to it."""

        if self.tabs.count() >= MAX_TABS:
            QMessageBox.warning(
                self,
                "Maximum Tabs",
                f"You can have a maximum of {MAX_TABS} tabs.",
            )
            return

        tab_index = self.create_note_tab(
            self.get_next_note_name()
        )

        self.tabs.setCurrentIndex(tab_index)


    def rename_tab(self, tab_index):
        """Rename the specified tab."""

        if tab_index < 0:
            return

        current_name = self.tabs.tabText(tab_index)

        new_name, accepted = QInputDialog.getText(
            self,
            "Rename Tab",
            "New tab name:",
            text=current_name,
        )

        if accepted and new_name.strip():
            self.tabs.setTabText(
                tab_index,
                new_name.strip(),
            )


    def rename_current_tab(self):
        """Rename the currently selected tab."""

        self.rename_tab(
            self.tabs.currentIndex()
        )


    def remove_current_tab(self):
        """Delete the current tab after confirmation."""

        current_index = self.tabs.currentIndex()

        if current_index < 0:
            return

        tab_name = self.tabs.tabText(current_index)

        confirm = QMessageBox.question(
            self,
            "Delete Tab",
            f"Delete tab '{tab_name}'?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            tab_widget = self.tabs.widget(current_index)

            self.tabs.removeTab(current_index)
            tab_widget.deleteLater()

            # Always keep at least one note available.
            if self.tabs.count() == 0:
                self.create_note_tab("Note 1")


    def rebuild_tab_menu(self):
        """Rebuild the Tab Options menu for the current tab."""

        self.tab_menu.clear()

        current_index = self.tabs.currentIndex()

        if current_index < 0:
            return

        current_name = self.tabs.tabText(current_index)

        add_action = QAction("Add New Tab", self)
        add_action.triggered.connect(self.add_new_tab)
        self.tab_menu.addAction(add_action)

        self.tab_menu.addSeparator()

        current_tab_header = QAction(
            f"Current Tab: {current_name}",
            self,
        )
        current_tab_header.setEnabled(False)
        self.tab_menu.addAction(current_tab_header)

        color_menu = self.tab_menu.addMenu("Color")

        for color_name, color_code in TAB_COLORS.items():
            color_action = QAction(color_name, self)

            if color_code:
                color_action.setIcon(
                    make_color_icon(color_code)
                )

            color_action.triggered.connect(
                lambda checked=False, selected_color=color_name:
                    self.apply_tab_color(selected_color)
            )

            color_menu.addAction(color_action)

        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(
            self.rename_current_tab
        )
        self.tab_menu.addAction(rename_action)

        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(
            self.clear_current_tab
        )
        self.tab_menu.addAction(clear_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(
            self.remove_current_tab
        )
        self.tab_menu.addAction(delete_action)

        self.tab_menu.addSeparator()

        go_to_menu = self.tab_menu.addMenu("Go To Tab")

        for index in range(self.tabs.count()):
            tab_name = self.tabs.tabText(index)

            tab_action = QAction(tab_name, self)
            tab_action.setCheckable(True)
            tab_action.setChecked(index == current_index)

            tab_action.triggered.connect(
                lambda checked=False, tab_index=index:
                    self.tabs.setCurrentIndex(tab_index)
            )

            go_to_menu.addAction(tab_action)


    def apply_tab_color(self, color_name):
        """Apply a selected color to the current tab and note background."""

        current_index = self.tabs.currentIndex()

        if current_index < 0:
            return

        self.tabs.tabBar().setTabData(
            current_index,
            color_name,
        )

        self.tabs.tabBar().update()
        self.apply_note_background(current_index)



    # Text Formatting Methods
    def toggle_bold(self, checked):
        """Toggle bold formatting for selected text or future typing."""

        editor = self.get_current_editor()
        cursor = editor.textCursor()
        fmt = QTextCharFormat()

        if cursor.hasSelection():
            is_bold = (
                cursor.charFormat().fontWeight()
                == QFont.Weight.Bold
            )

            fmt.setFontWeight(
                QFont.Weight.Normal
                if is_bold
                else QFont.Weight.Bold
            )

            cursor.mergeCharFormat(fmt)

            cursor.clearSelection()
            editor.setTextCursor(cursor)

            normal_fmt = QTextCharFormat()
            normal_fmt.setFontWeight(QFont.Weight.Normal)
            editor.mergeCurrentCharFormat(normal_fmt)

            self.bold_button.setChecked(False)

        else:
            fmt.setFontWeight(
                QFont.Weight.Bold
                if checked
                else QFont.Weight.Normal
            )

            editor.mergeCurrentCharFormat(fmt)

        editor.setFocus()


    def toggle_italic(self, checked):
        """Toggle italic formatting for selected text or future typing."""

        editor = self.get_current_editor()
        cursor = editor.textCursor()
        fmt = QTextCharFormat()

        if cursor.hasSelection():
            is_italic = cursor.charFormat().fontItalic()
            fmt.setFontItalic(not is_italic)

            cursor.mergeCharFormat(fmt)

            cursor.clearSelection()
            editor.setTextCursor(cursor)

            normal_fmt = QTextCharFormat()
            normal_fmt.setFontItalic(False)
            editor.mergeCurrentCharFormat(normal_fmt)

            self.italic_button.setChecked(False)

        else:
            fmt.setFontItalic(checked)
            editor.mergeCurrentCharFormat(fmt)

        editor.setFocus()


    def toggle_underline(self, checked):
        """Toggle underline formatting for selected text or future typing."""

        editor = self.get_current_editor()
        cursor = editor.textCursor()
        fmt = QTextCharFormat()

        if cursor.hasSelection():
            is_underlined = cursor.charFormat().fontUnderline()
            fmt.setFontUnderline(not is_underlined)

            cursor.mergeCharFormat(fmt)

            cursor.clearSelection()
            editor.setTextCursor(cursor)

            normal_fmt = QTextCharFormat()
            normal_fmt.setFontUnderline(False)
            editor.mergeCurrentCharFormat(normal_fmt)

            self.underline_button.setChecked(False)

        else:
            fmt.setFontUnderline(checked)
            editor.mergeCurrentCharFormat(fmt)

        editor.setFocus()


    def toggle_strike(self, checked):
        """Toggle strikethrough formatting for selected text or future typing."""

        editor = self.get_current_editor()
        cursor = editor.textCursor()
        fmt = QTextCharFormat()

        if cursor.hasSelection():
            is_struck = cursor.charFormat().fontStrikeOut()
            fmt.setFontStrikeOut(not is_struck)

            cursor.mergeCharFormat(fmt)

            cursor.clearSelection()
            editor.setTextCursor(cursor)

            normal_fmt = QTextCharFormat()
            normal_fmt.setFontStrikeOut(False)
            editor.mergeCurrentCharFormat(normal_fmt)

            self.strike_button.setChecked(False)

        else:
            fmt.setFontStrikeOut(checked)
            editor.mergeCurrentCharFormat(fmt)

        editor.setFocus()


    def indent_forward(self):
        """Increase indentation for the current paragraph(s)."""

        self.adjust_indent(1)


    def indent_backward(self):
        """Decrease indentation for the current paragraph(s)."""

        self.adjust_indent(-1)


    def apply_text_style(self, style_name):
        """Apply a predefined text style."""

        if style_name == "Text Style":
            return

        editor = self.get_current_editor()
        cursor = editor.textCursor()

        styles = {
            "Title": (20, QFont.Weight.Bold),
            "Heading": (16, QFont.Weight.Bold),
            "Subheading": (13, QFont.Weight.Bold),
            "Body": (DEFAULT_FONT_SIZE, QFont.Weight.Normal),
        }

        size, weight = styles[style_name]

        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        fmt.setFontWeight(weight)

        has_selection = cursor.hasSelection()

        cursor.mergeCharFormat(fmt)
        cursor.mergeBlockCharFormat(fmt)
        editor.mergeCurrentCharFormat(fmt)

        # After styling selected text, return future typing to Body style.
        if has_selection:
            cursor.clearSelection()
            editor.setTextCursor(cursor)

            body_fmt = QTextCharFormat()
            body_fmt.setFontPointSize(DEFAULT_FONT_SIZE)
            body_fmt.setFontWeight(QFont.Weight.Normal)

            editor.mergeCurrentCharFormat(body_fmt)

        self.style_dropdown.blockSignals(True)
        self.style_dropdown.setCurrentIndex(0)
        self.style_dropdown.blockSignals(False)

        editor.setFocus()


    def apply_text_color(self, color_name):
        """Apply a selected text color."""

        if color_name == "Text Color":
            return

        editor = self.get_current_editor()
        cursor = editor.textCursor()

        color_code = TEXT_COLORS[color_name]

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_code))

        has_selection = cursor.hasSelection()

        cursor.mergeCharFormat(fmt)
        editor.mergeCurrentCharFormat(fmt)

        # After coloring selected text, return future typing to black.
        if has_selection:
            cursor.clearSelection()
            editor.setTextCursor(cursor)

            normal_color = QTextCharFormat()
            normal_color.setForeground(
                QColor(TEXT_COLORS["Black"])
            )

            editor.mergeCurrentCharFormat(normal_color)

        self.color_dropdown.blockSignals(True)
        self.color_dropdown.setCurrentIndex(0)
        self.color_dropdown.blockSignals(False)

        editor.setFocus()


    def apply_list_style(self, index):
        """Apply or remove a bullet or numbered list style."""

        list_name = self.list_dropdown.itemData(index)

        if list_name is None:
            return

        editor = self.get_current_editor()
        cursor = editor.textCursor()

        list_styles = {
            "Circle": QTextListFormat.Style.ListDisc,
            "Square": QTextListFormat.Style.ListSquare,
            "Numbered": QTextListFormat.Style.ListDecimal,
        }

        selected_style = list_styles[list_name]
        current_list = cursor.currentList()

        if (
            current_list
            and current_list.format().style() == selected_style
        ):
            document = editor.document()

            start = cursor.selectionStart()

            if cursor.hasSelection():
                end = cursor.selectionEnd() - 1
            else:
                end = cursor.position()

            block = document.findBlock(start)
            last_block = document.findBlock(end)

            blocks_to_remove = []

            while block.isValid():
                blocks_to_remove.append(block)

                if block == last_block:
                    break

                block = block.next()

            for block in blocks_to_remove:
                text_list = block.textList()

                if text_list:
                    text_list.remove(block)

        else:
            list_format = QTextListFormat()
            list_format.setStyle(selected_style)
            cursor.createList(list_format)

        self.list_dropdown.blockSignals(True)
        self.list_dropdown.setCurrentIndex(0)
        self.list_dropdown.blockSignals(False)

        editor.setFocus()


    def clear_current_tab(self):
        """Clear the current note after confirmation."""

        editor = self.get_current_editor()

        confirm = QMessageBox.question(
            self,
            "Clear Tab",
            "Clear all text in this tab?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            editor.clear()
            editor.setFocus()


    # Persistence Methods
    def save_notes(self, show_error=True):
        """
        Collect the current application state and save it to disk.
        Returns True on success and False if writing to disk fails.
        """

        tabs_data = []

        for index in range(self.tabs.count()):
            editor = self.tabs.widget(index)

            tabs_data.append(
                {
                    "name": self.tabs.tabText(index),
                    "content": editor.toHtml(),
                    "color": self.tabs.tabBar().tabData(index) or "None",
                }
            )

        data = {
            "current_tab": self.tabs.currentIndex(),
            "tabs": tabs_data,
        }


        try:
            save_data(data)

            # Allow a future error message if saving later fails again.
            self.save_error_shown = False
            return True

        except OSError as error:
            if show_error and not self.save_error_shown:
                QMessageBox.critical(
                    self,
                    "Save Error",
                    (
                        "StickyTabs could not save your notes.\n\n"
                        "Please check that the storage location is available "
                        "and writable.\n\n"
                        f"Details: {error}"
                    ),
                )

                self.save_error_shown = True

            return False


    def load_notes(self):
        """Restore saved tabs or create a new blank note."""

        data = load_data()

        if data is None:
            self.create_note_tab("Note 1")
            return

        tabs_data = data.get("tabs", [])

        if not isinstance(tabs_data, list) or not tabs_data:
            self.create_note_tab("Note 1")
            return

        for tab_data in tabs_data[:MAX_TABS]:
            if not isinstance(tab_data, dict):
                continue

            self.create_note_tab(
                name=tab_data.get(
                    "name",
                    self.get_next_note_name(),
                ),
                content=tab_data.get("content", ""),
                color_name=tab_data.get("color", "None"),
            )

        # Ensure the application always has at least one usable tab.
        if self.tabs.count() == 0:
            self.create_note_tab("Note 1")
            return

        saved_index = data.get("current_tab", 0)

        if (
            isinstance(saved_index, int)
            and 0 <= saved_index < self.tabs.count()
        ):
            self.tabs.setCurrentIndex(saved_index)

        
    def closeEvent(self, event):
        """Save the latest application state before closing."""

        if self.save_notes(show_error=False):
            event.accept()
            return

        confirm = QMessageBox.question(
            self,
            "Close Without Saving?",
            (
                "StickyTabs could not save your latest changes.\n\n"
                "Close the application anyway?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()