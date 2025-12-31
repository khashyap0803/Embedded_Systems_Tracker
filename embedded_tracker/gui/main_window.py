"""Qt-based GUI for the Embedded Tracker application.

This is the refactored main window that imports tabs from modular tab files.
The "God class" has been decomposed into:
- gui/base.py: Shared components (BaseCrudTab, FormDialog, etc.)
- gui/tabs/: Individual tab modules (phases, weeks, days, etc.)
- gui/workers.py: Background threading utilities
- This file: MainWindow and app entry point
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QSettings, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsOpacityEffect,
    QMainWindow,
    QMessageBox,
    QTabWidget,
)

from ..db import ensure_seed_data, init_db
from .. import services
from ..export import export_tasks_csv, export_roadmap_csv, export_tasks_pdf, export_roadmap_pdf, ExportError

# Import shared base components
from .base import BaseCrudTab, DARK_THEME, LIGHT_THEME

# Import all tabs from the tabs package
from .tabs import (
    PhasesTab,
    WeeksTab,
    DaysTab,
    HoursTab,
    ResourcesTab,
    ProjectsTab,
    CertificationsTab,
    ApplicationsTab,
    MetricsTab,
    HardwareTab,
)


class MainWindow(QMainWindow):
    """Primary application window hosting all management tabs."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Embedded Tracker")
        self.resize(1280, 800)
        
        # Settings for persistence
        self.settings = QSettings("EmbeddedTracker", "EmbeddedTracker")
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create tabs
        self.tabs = QTabWidget()

        self.phases_tab = PhasesTab(self)
        self.weeks_tab = WeeksTab(self)
        self.days_tab = DaysTab(self)
        self.hours_tab = HoursTab(self)
        self.resources_tab = ResourcesTab(self)
        self.projects_tab = ProjectsTab(self)
        self.certifications_tab = CertificationsTab(self)
        self.applications_tab = ApplicationsTab(self)
        self.metrics_tab = MetricsTab(self)
        self.hardware_tab = HardwareTab(self)

        self.tabs.addTab(self.phases_tab, "Phases")
        self.tabs.addTab(self.weeks_tab, "Weeks")
        self.tabs.addTab(self.days_tab, "Days")
        self.tabs.addTab(self.hours_tab, "Hours")
        self.tabs.addTab(self.resources_tab, "Resources")
        self.tabs.addTab(self.projects_tab, "Projects")
        self.tabs.addTab(self.certifications_tab, "Certifications")
        self.tabs.addTab(self.applications_tab, "Applications")
        self.tabs.addTab(self.metrics_tab, "Metrics")
        self.tabs.addTab(self.hardware_tab, "🔧 Hardware")

        self.setCentralWidget(self.tabs)
        
        # Connect smooth animation for tab switching
        self.tabs.currentChanged.connect(self._animate_tab_change)
        
        # Apply saved theme
        self._apply_theme(self.settings.value("theme", "dark"))
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Initial data load - refresh all tabs on startup
        self._initial_load_done = False
    
    def _setup_keyboard_shortcuts(self) -> None:
        """Setup global keyboard shortcuts for common actions."""
        from PySide6.QtGui import QShortcut
        
        # Store shortcuts as instance variables to prevent garbage collection
        self._shortcuts = []
        
        # Ctrl+N - Add new item in current tab
        add_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        add_shortcut.activated.connect(self._shortcut_add)
        add_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcuts.append(add_shortcut)
        
        # Ctrl+E - Edit selected item
        edit_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        edit_shortcut.activated.connect(self._shortcut_edit)
        edit_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcuts.append(edit_shortcut)
        
        # Delete - Delete selected item
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self._shortcut_delete)
        delete_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcuts.append(delete_shortcut)
        
        # Ctrl+R - Refresh current tab
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self._shortcut_refresh)
        refresh_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcuts.append(refresh_shortcut)
        
        # Ctrl+Shift+A - Refresh ALL tabs
        refresh_all_shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), self)
        refresh_all_shortcut.activated.connect(self._shortcut_refresh_all)
        refresh_all_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcuts.append(refresh_all_shortcut)
        
        # Escape - Clear selection / close dialogs
        escape_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        escape_shortcut.activated.connect(self._shortcut_escape)
        escape_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcuts.append(escape_shortcut)
        
        # Ctrl+Tab - Next tab
        next_tab_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_tab_shortcut.activated.connect(self._shortcut_next_tab)
        next_tab_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcuts.append(next_tab_shortcut)
        
        # Ctrl+Shift+Tab - Previous tab
        prev_tab_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_tab_shortcut.activated.connect(self._shortcut_prev_tab)
        prev_tab_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcuts.append(prev_tab_shortcut)
        
        # Ctrl+1 through Ctrl+9 - Switch to tab by number
        for i in range(1, 10):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            shortcut.activated.connect(lambda idx=i-1: self._shortcut_go_to_tab(idx))
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            self._shortcuts.append(shortcut)
    
    def _get_current_crud_tab(self) -> Optional[BaseCrudTab]:
        """Get the current tab if it's a CRUD tab."""
        current = self.tabs.currentWidget()
        if isinstance(current, BaseCrudTab):
            return current
        return None
    
    def _shortcut_add(self) -> None:
        """Handle Ctrl+N shortcut."""
        tab = self._get_current_crud_tab()
        if tab:
            tab.handle_add()
    
    def _shortcut_edit(self) -> None:
        """Handle Ctrl+E shortcut."""
        tab = self._get_current_crud_tab()
        if tab:
            tab.handle_edit()
    
    def _shortcut_delete(self) -> None:
        """Handle Delete shortcut."""
        tab = self._get_current_crud_tab()
        if tab:
            tab.handle_delete()
    
    def _shortcut_refresh(self) -> None:
        """Handle Ctrl+R - refresh current tab only."""
        tab = self._get_current_crud_tab()
        if tab:
            tab.refresh()
            self.statusBar().showMessage("Tab refreshed!", 2000)
    
    def _shortcut_refresh_all(self) -> None:
        """Handle Ctrl+Shift+A - refresh ALL tabs."""
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, BaseCrudTab):
                tab.refresh()
        self.statusBar().showMessage("All tabs refreshed!", 2000)
    
    def _shortcut_escape(self) -> None:
        """Handle Escape shortcut - clear selection."""
        tab = self._get_current_crud_tab()
        if tab and hasattr(tab, 'table'):
            tab.table.clearSelection()
    
    def _shortcut_next_tab(self) -> None:
        """Handle Ctrl+Tab - go to next tab."""
        current = self.tabs.currentIndex()
        next_idx = (current + 1) % self.tabs.count()
        self.tabs.setCurrentIndex(next_idx)
    
    def _shortcut_prev_tab(self) -> None:
        """Handle Ctrl+Shift+Tab - go to previous tab."""
        current = self.tabs.currentIndex()
        prev_idx = (current - 1) % self.tabs.count()
        self.tabs.setCurrentIndex(prev_idx)
    
    def _shortcut_go_to_tab(self, idx: int) -> None:
        """Handle Ctrl+1-9 - go to specific tab."""
        if 0 <= idx < self.tabs.count():
            self.tabs.setCurrentIndex(idx)
    
    def _create_menu_bar(self) -> None:
        """Create the main menu bar with File, View, Help menus."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Export submenu
        export_menu = file_menu.addMenu("📤 Export")
        
        export_tasks_csv_action = QAction("Export Tasks (CSV)", self)
        export_tasks_csv_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        export_tasks_csv_action.setStatusTip("Export all tasks to CSV file")
        export_tasks_csv_action.triggered.connect(self._export_tasks_csv)
        export_menu.addAction(export_tasks_csv_action)
        
        export_tasks_pdf_action = QAction("Export Tasks (PDF)", self)
        export_tasks_pdf_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        export_tasks_pdf_action.setStatusTip("Export all tasks to PDF file")
        export_tasks_pdf_action.triggered.connect(self._export_tasks_pdf)
        export_menu.addAction(export_tasks_pdf_action)
        
        export_menu.addSeparator()
        
        export_roadmap_csv_action = QAction("Export Roadmap (CSV)", self)
        export_roadmap_csv_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        export_roadmap_csv_action.setStatusTip("Export roadmap overview to CSV")
        export_roadmap_csv_action.triggered.connect(self._export_roadmap_csv)
        export_menu.addAction(export_roadmap_csv_action)
        
        export_roadmap_pdf_action = QAction("Export Roadmap (PDF)", self)
        export_roadmap_pdf_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        export_roadmap_pdf_action.setStatusTip("Export roadmap to PDF")
        export_roadmap_pdf_action.triggered.connect(self._export_roadmap_pdf)
        export_menu.addAction(export_roadmap_pdf_action)
        
        file_menu.addSeparator()
        
        # Backup & Restore submenu
        backup_menu = file_menu.addMenu("💾 Backup & Restore")
        
        backup_action = QAction("📥 Create Backup...", self)
        backup_action.setShortcut(QKeySequence("Ctrl+B"))
        backup_action.setStatusTip("Export entire database to JSON backup file")
        backup_action.triggered.connect(self._create_backup)
        backup_menu.addAction(backup_action)
        
        restore_action = QAction("📤 Restore from Backup...", self)
        restore_action.setStatusTip("Restore database from a JSON backup file (WARNING: Overwrites data!)")
        restore_action.triggered.connect(self._restore_backup)
        backup_menu.addAction(restore_action)
        
        file_menu.addSeparator()
        
        refresh_action = QAction("🔄 Refresh All", self)
        refresh_action.setShortcut(QKeySequence("Ctrl+Shift+A"))
        refresh_action.setStatusTip("Refresh all tabs")
        refresh_action.triggered.connect(self._refresh_all)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("❌ Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        # Themes submenu
        themes_menu = view_menu.addMenu("🎨 Themes")
        
        self.light_theme_action = QAction("☀️ Dawn Theme (Light)", self, checkable=True)
        self.light_theme_action.setStatusTip("Apply warm dawn/coral light theme")
        self.light_theme_action.triggered.connect(lambda: self._apply_theme("light"))
        themes_menu.addAction(self.light_theme_action)
        
        self.dark_theme_action = QAction("🔥 Ember Theme (Dark)", self, checkable=True)
        self.dark_theme_action.setStatusTip("Apply intense ember/orange dark theme")
        self.dark_theme_action.triggered.connect(lambda: self._apply_theme("dark"))
        themes_menu.addAction(self.dark_theme_action)
        
        view_menu.addSeparator()
        
        toggle_theme_action = QAction("🔄 Toggle Theme", self)
        toggle_theme_action.setShortcut(QKeySequence("Ctrl+D"))
        toggle_theme_action.setStatusTip("Switch between light and dark themes")
        toggle_theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(toggle_theme_action)
        
        view_menu.addSeparator()
        
        autofit_action = QAction("📐 Auto-Fit Columns", self)
        autofit_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        autofit_action.setStatusTip("Resize columns to fit content")
        autofit_action.triggered.connect(self._autofit_columns)
        view_menu.addAction(autofit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        about_action = QAction("ℹ️ About", self)
        about_action.setStatusTip("About Embedded Tracker")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        shortcuts_action = QAction("⌨️ Keyboard Shortcuts", self)
        shortcuts_action.setShortcut(QKeySequence("Ctrl+/"))
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)

    def _apply_theme(self, theme: str) -> None:
        """Apply the specified theme (dark or light)."""
        app = QApplication.instance()
        if app:
            if theme == "dark":
                app.setStyleSheet(DARK_THEME)
                self.dark_theme_action.setChecked(True)
                self.light_theme_action.setChecked(False)
                self._current_theme = "dark"
            else:
                app.setStyleSheet(LIGHT_THEME)
                self.dark_theme_action.setChecked(False)
                self.light_theme_action.setChecked(True)
                self._current_theme = "light"
            self.settings.setValue("theme", theme)
    
    def _toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        current = getattr(self, "_current_theme", "dark")
        new_theme = "light" if current == "dark" else "dark"
        self._apply_theme(new_theme)
    
    def _animate_tab_change(self, index: int) -> None:
        """Fade in the new tab content with a smooth animation."""
        widget = self.tabs.widget(index)
        if widget:
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(450)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.InOutCubic)
            anim.start()
            
            widget._anim = anim

    def resizeEvent(self, event) -> None:
        """Handle window resize to auto-fit columns."""
        super().resizeEvent(event)
        self._autofit_columns()
    
    def _autofit_columns(self) -> None:
        """Auto-fit columns intelligently."""
        current_tab = self.tabs.currentWidget()
        if hasattr(current_tab, "table"):
            table = current_tab.table
            table.resizeColumnsToContents()
            table.resizeRowsToContents()
            
            col_count = table.columnCount()
            if col_count == 0:
                return
                
            for col in range(col_count):
                current = table.columnWidth(col)
                table.setColumnWidth(col, current + 24)

    def _refresh_all(self) -> None:
        """Refresh all tabs."""
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if hasattr(tab, "refresh"):
                tab.refresh()
        QMessageBox.information(self, "Refreshed", "All tabs have been refreshed.")

    def _export_tasks_csv(self) -> None:
        """Export tasks to CSV file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Tasks to CSV", "tasks_export.csv", "CSV Files (*.csv)"
        )
        if path:
            try:
                tasks = services.list_tasks()
                export_tasks_csv(tasks, path)
                QMessageBox.information(self, "Success", f"Tasks exported to:\n{path}")
            except ExportError as e:
                QMessageBox.critical(self, "Export Error", str(e))
    
    def _export_tasks_pdf(self) -> None:
        """Export tasks to PDF file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Tasks to PDF", "tasks_export.pdf", "PDF Files (*.pdf)"
        )
        if path:
            try:
                tasks = services.list_tasks()
                export_tasks_pdf(tasks, path)
                QMessageBox.information(self, "Success", f"Tasks exported to:\n{path}")
            except ExportError as e:
                QMessageBox.critical(self, "Export Error", str(e))
    
    def _export_roadmap_csv(self) -> None:
        """Export roadmap to CSV file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Roadmap to CSV", "roadmap_export.csv", "CSV Files (*.csv)"
        )
        if path:
            try:
                phases = services.list_phases()
                weeks = services.list_weeks()
                export_roadmap_csv(phases, weeks, path)
                QMessageBox.information(self, "Success", f"Roadmap exported to:\n{path}")
            except ExportError as e:
                QMessageBox.critical(self, "Export Error", str(e))
    
    def _export_roadmap_pdf(self) -> None:
        """Export roadmap to PDF file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Roadmap to PDF", "roadmap_export.pdf", "PDF Files (*.pdf)"
        )
        if path:
            try:
                phases = services.list_phases()
                weeks = services.list_weeks()
                export_roadmap_pdf(phases, weeks, path)
                QMessageBox.information(self, "Success", f"Roadmap exported to:\n{path}")
            except ExportError as e:
                QMessageBox.critical(self, "Export Error", str(e))
    
    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Embedded Tracker",
            "<h2>🔧 Embedded Systems Tracker</h2>"
            "<p><b>Version 1.0.0</b></p>"
            "<p>A professional roadmap tracking application for embedded systems mastery.</p>"
            "<p><b>✨ Features:</b></p>"
            "<ul>"
            "<li>📅 59-week learning roadmap with 6 buffer weeks</li>"
            "<li>⏱️ Dynamic scheduling (dates calculated on first task start)</li>"
            "<li>🔄 Plan vs Actual date comparison for efficiency tracking</li>"
            "<li>💼 Project portfolio management</li>"
            "<li>📜 Certification progress tracking</li>"
            "<li>📝 Job application tracker</li>"
            "<li>🛒 Hardware inventory with BOM comparison</li>"
            "<li>📊 CSV and PDF export support</li>"
            "</ul>"
            "<p>© 2025 Khashyap</p>"
        )
    
    def _show_shortcuts(self) -> None:
        """Show keyboard shortcuts dialog."""
        QMessageBox.information(
            self,
            "Keyboard Shortcuts",
            "<h3>⌨️ Keyboard Shortcuts</h3>"
            "<table>"
            "<tr><td colspan='2'><b>— General —</b></td></tr>"
            "<tr><td><b>Ctrl+/</b></td><td>Show Shortcuts</td></tr>"
            "<tr><td><b>Ctrl+Shift+A</b></td><td>Refresh All Tabs</td></tr>"
            "<tr><td><b>Ctrl+R</b></td><td>Refresh Current Tab</td></tr>"
            "<tr><td colspan='2'><b>— Navigation —</b></td></tr>"
            "<tr><td><b>Ctrl+Tab</b></td><td>Next Tab</td></tr>"
            "<tr><td><b>Ctrl+Shift+Tab</b></td><td>Previous Tab</td></tr>"
            "<tr><td><b>Ctrl+1-9</b></td><td>Go to Tab 1-9</td></tr>"
            "<tr><td colspan='2'><b>— CRUD —</b></td></tr>"
            "<tr><td><b>Ctrl+N</b></td><td>Add New Item</td></tr>"
            "<tr><td><b>Ctrl+E</b></td><td>Edit Selected Item</td></tr>"
            "<tr><td><b>Delete</b></td><td>Delete Selected Item</td></tr>"
            "<tr><td><b>Escape</b></td><td>Clear Selection</td></tr>"
            "<tr><td colspan='2'><b>— Export —</b></td></tr>"
            "<tr><td><b>Ctrl+Shift+T</b></td><td>Export Tasks (CSV)</td></tr>"
            "<tr><td><b>Ctrl+Shift+P</b></td><td>Export Tasks (PDF)</td></tr>"
            "<tr><td><b>Ctrl+Shift+R</b></td><td>Export Roadmap (CSV)</td></tr>"
            "<tr><td><b>Ctrl+Shift+O</b></td><td>Export Roadmap (PDF)</td></tr>"
            "<tr><td colspan='2'><b>— View —</b></td></tr>"
            "<tr><td><b>Ctrl+D</b></td><td>Toggle Dark Mode</td></tr>"
            "<tr><td><b>Ctrl+Shift+F</b></td><td>Auto-Fit Columns</td></tr>"
            "</table>"
        )

    def _create_backup(self) -> None:
        """Create a JSON backup of the entire database."""
        from datetime import datetime
        default_name = f"embedded_tracker_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Create Backup",
            default_name,
            "JSON Files (*.json)"
        )
        if path:
            try:
                result_path = services.backup_database_to_json(path)
                QMessageBox.information(
                    self,
                    "Backup Complete",
                    f"✅ Database backed up successfully!\n\nFile: {result_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Backup Error", f"Failed to create backup:\n{e}")
    
    def _restore_backup(self) -> None:
        """Restore database from a JSON backup file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Restore from Backup",
            "",
            "JSON Files (*.json)"
        )
        if path:
            # Confirm before restore
            confirm = QMessageBox.warning(
                self,
                "⚠️ Confirm Restore",
                "WARNING: This will ADD data from the backup to your database.\n\n"
                "Existing data will NOT be deleted, but duplicates may be created.\n\n"
                "Are you sure you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if confirm != QMessageBox.Yes:
                return
            
            try:
                summary = services.restore_database_from_json(path)
                summary_text = "\n".join([f"  {k}: {v}" for k, v in summary.items() if v > 0])
                QMessageBox.information(
                    self,
                    "Restore Complete",
                    f"✅ Database restored successfully!\n\nRecords imported:\n{summary_text}"
                )
                # Refresh all tabs
                self._refresh_all()
            except FileNotFoundError as e:
                QMessageBox.critical(self, "File Not Found", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Restore Error", f"Failed to restore:\n{e}")

    def refresh_hierarchy(self) -> None:
        """Refresh hierarchy tabs (phases, weeks, days)."""
        self.phases_tab.refresh()
        self.weeks_tab.refresh()
        self.days_tab.refresh()

    def showEvent(self, event) -> None:
        """Handle window show - load initial data."""
        super().showEvent(event)
        if not self._initial_load_done:
            self._initial_load_done = True
            # Refresh all tabs on first show
            for i in range(self.tabs.count()):
                tab = self.tabs.widget(i)
                if hasattr(tab, "refresh"):
                    tab.refresh()

    def keyPressEvent(self, event) -> None:
        """Handle key press events for global shortcuts."""
        modifiers = event.modifiers()
        key = event.key()
        
        # Ctrl+Shift+A - Refresh ALL tabs
        if modifiers == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier) and key == Qt.Key.Key_A:
            self._shortcut_refresh_all()
            event.accept()
            return
        
        # Ctrl+Shift+T - Export Tasks CSV  
        if modifiers == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier) and key == Qt.Key.Key_T:
            self._export_tasks_csv()
            event.accept()
            return
        
        # Ctrl+Shift+P - Export Tasks PDF
        if modifiers == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier) and key == Qt.Key.Key_P:
            self._export_tasks_pdf()
            event.accept()
            return
        
        # Ctrl+Shift+O - Export Roadmap PDF
        if modifiers == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier) and key == Qt.Key.Key_O:
            self._export_roadmap_pdf()
            event.accept()
            return
        
        super().keyPressEvent(event)
    
    def closeEvent(self, event) -> None:
        """Confirm before closing if there are running timers."""
        hours_tab = self.hours_tab
        if hasattr(hours_tab, '_records'):
            running = [r for r in hours_tab._records if getattr(r, 'is_running', False)]
            if running:
                reply = QMessageBox.question(
                    self,
                    "Confirm Exit",
                    f"You have {len(running)} running timer(s).\n\nAre you sure you want to exit?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    event.ignore()
                    return
        event.accept()


def run() -> None:
    """Initialise the database and start the Qt event loop."""
    init_db()
    ensure_seed_data()
    services.reset_stale_tasks()  # Fix Zombie Timer bug on startup
    app = QApplication.instance() or QApplication([])
    
    # Set application metadata
    app.setApplicationName("Embedded Tracker")
    app.setOrganizationName("EmbeddedTracker")
    app.setApplicationVersion("1.0")
    
    window = MainWindow()
    window.show()
    app.exec()
