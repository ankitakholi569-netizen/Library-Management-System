"""
Books Widget — Full CRUD for Library Book Catalog.
Course: BBAT104 — Total Quality Management.

Features:
  - Instant search bar with live filtering (title/author/ISBN/category)
  - Category + availability filter dropdowns
  - Sortable multi-column table with latency KPI display
  - Add Book / Edit Book dialogs with full validation
  - Delete with active-loan guard
  - TQM defect flag toggle
  - Export Catalog to Excel
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QDialog, QFormLayout, QSpinBox, QCheckBox,
    QMessageBox, QFrame, QDialogButtonBox, QTextEdit, QAbstractItemView,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from services.library_service import (
    get_all_books, get_book_categories, add_book, update_book,
    delete_book, get_book_by_id,
)
from services.search_service import search_books
from services.report_service import generate_catalog_excel
from services.logger_service import get_logger

logger = get_logger("gui.books_widget")

# ── Shared style helpers ──────────────────────────────────────────────────────
_BTN_PRIMARY = "background-color:#2563EB;color:#fff;font-weight:700;padding:8px 16px;border-radius:6px;border:none;"
_BTN_SUCCESS = "background-color:#10B981;color:#fff;font-weight:700;padding:8px 16px;border-radius:6px;border:none;"
_BTN_DANGER  = "background-color:#EF4444;color:#fff;font-weight:700;padding:8px 14px;border-radius:6px;border:none;"
_BTN_DARK    = "background-color:#0F172A;color:#fff;font-weight:700;padding:8px 16px;border-radius:6px;border:none;"
_BTN_WARN    = "background-color:#F59E0B;color:#fff;font-weight:700;padding:8px 14px;border-radius:6px;border:none;"


# ══════════════════════════════════════════════════════════════════════════════
# ADD / EDIT BOOK DIALOG
# ══════════════════════════════════════════════════════════════════════════════
class BookDialog(QDialog):
    """Modal dialog for adding or editing a book record."""

    def __init__(self, book_data: dict = None, parent=None):
        super().__init__(parent)
        self.book_data = book_data  # None = add mode
        self.setWindowTitle("Add New Book" if not book_data else f"Edit Book — ID #{book_data['id']}")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._build_ui()
        if book_data:
            self._populate(book_data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Title
        mode_title = "Add New Book to Catalog" if not self.book_data else "Edit Book Record"
        title_lbl = QLabel(mode_title)
        title_lbl.setStyleSheet("font-size:18px;font-weight:800;color:#0F172A;")
        layout.addWidget(title_lbl)

        # Form
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.f_title    = QLineEdit(); self.f_title.setPlaceholderText("e.g. Introduction to Algorithms")
        self.f_author   = QLineEdit(); self.f_author.setPlaceholderText("e.g. Cormen, Leiserson, Rivest")
        self.f_isbn     = QLineEdit(); self.f_isbn.setPlaceholderText("e.g. 978-0-262-03384-8")
        self.f_category = QComboBox()
        self.f_category.setEditable(True)
        cats = ["Computer Science", "Electronics", "Mathematics", "Mechanical Engineering",
                "Civil Engineering", "Management", "Science", "Artificial Intelligence", "General"]
        self.f_category.addItems(cats)

        self.f_year   = QSpinBox(); self.f_year.setRange(1900, 2099); self.f_year.setValue(2024)
        self.f_copies = QSpinBox(); self.f_copies.setRange(1, 999);   self.f_copies.setValue(1)
        self.f_shelf  = QLineEdit(); self.f_shelf.setPlaceholderText("e.g. Aisle 1 - Rack A")
        self.f_defect = QCheckBox("Mark as defective (TQM inspection failed)")
        self.f_defect.setStyleSheet("color:#EF4444;font-weight:600;")
        self.f_notes  = QTextEdit(); self.f_notes.setPlaceholderText("Defect notes (optional)...")
        self.f_notes.setMaximumHeight(70)

        form.addRow("Title *",          self.f_title)
        form.addRow("Author(s) *",      self.f_author)
        form.addRow("ISBN *",           self.f_isbn)
        form.addRow("Category",         self.f_category)
        form.addRow("Year Published",   self.f_year)
        form.addRow("Total Copies",     self.f_copies)
        form.addRow("Shelf Location",   self.f_shelf)
        form.addRow("",                 self.f_defect)
        form.addRow("Defect Notes",     self.f_notes)

        layout.addLayout(form)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Save).setStyleSheet(_BTN_PRIMARY)
        btns.button(QDialogButtonBox.Cancel).setStyleSheet("padding:8px 14px;border-radius:6px;")
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _populate(self, d: dict):
        self.f_title.setText(d.get("title", ""))
        self.f_author.setText(d.get("author", ""))
        self.f_isbn.setText(d.get("isbn", ""))
        idx = self.f_category.findText(d.get("category", ""))
        if idx >= 0:
            self.f_category.setCurrentIndex(idx)
        else:
            self.f_category.setCurrentText(d.get("category", ""))
        self.f_year.setValue(d.get("year", 2024))
        self.f_copies.setValue(d.get("total_copies", 1))
        self.f_shelf.setText(d.get("shelf_location", ""))
        self.f_defect.setChecked(bool(d.get("defect_flag", False)))
        self.f_notes.setPlainText(d.get("defect_notes", ""))

    def _validate_and_accept(self):
        if not self.f_title.text().strip():
            QMessageBox.warning(self, "Validation Error", "Book title is required.")
            return
        if not self.f_author.text().strip():
            QMessageBox.warning(self, "Validation Error", "Author name is required.")
            return
        if not self.f_isbn.text().strip():
            QMessageBox.warning(self, "Validation Error", "ISBN is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "title":         self.f_title.text().strip(),
            "author":        self.f_author.text().strip(),
            "isbn":          self.f_isbn.text().strip(),
            "category":      self.f_category.currentText().strip(),
            "year":          self.f_year.value(),
            "total_copies":  self.f_copies.value(),
            "shelf_location": self.f_shelf.text().strip() or "Aisle 1 - Rack A",
            "defect_flag":   self.f_defect.isChecked(),
            "defect_notes":  self.f_notes.toPlainText().strip(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# BOOKS WIDGET — MAIN VIEW
# ══════════════════════════════════════════════════════════════════════════════
class BooksWidget(QWidget):
    """
    Full CRUD Book Catalog panel with instant search, filters, sorting,
    defect tagging, and Excel export.
    """

    COLS = ["ID", "Title", "Author(s)", "Category", "ISBN", "Year",
            "Avail / Total", "Shelf Location", "Quality Status"]

    def __init__(self, current_user: dict = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {"username": "admin", "role": "Chief Librarian"}
        self._books_cache: list = []
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        tb = QVBoxLayout(); tb.setSpacing(2)
        t = QLabel("Book Catalog Management")
        t.setStyleSheet("font-size:22px;font-weight:800;color:#0F172A;")
        s = QLabel("Add, edit, search and inspect all library books | TQM Quality Goal 1 — Faster Search & Retrieval")
        s.setStyleSheet("font-size:13px;color:#64748B;")
        tb.addWidget(t); tb.addWidget(s)
        hdr.addLayout(tb); hdr.addStretch()

        self.add_btn    = QPushButton("+ Add Book");     self.add_btn.setStyleSheet(_BTN_SUCCESS)
        self.export_btn = QPushButton("Export Excel");   self.export_btn.setStyleSheet(_BTN_DARK)
        self.refresh_btn= QPushButton("Refresh");        self.refresh_btn.setStyleSheet("padding:8px 14px;border-radius:6px;")
        hdr.addWidget(self.add_btn); hdr.addWidget(self.export_btn); hdr.addWidget(self.refresh_btn)
        root.addLayout(hdr)

        # ── Search + Filter bar ───────────────────────────────────────────────
        fbar = QHBoxLayout(); fbar.setSpacing(10)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by Title, Author, ISBN or Category...")
        self.search_box.setStyleSheet("padding:8px 12px;border-radius:6px;border:1.5px solid #E2E8F0;font-size:13px;")
        self.search_box.textChanged.connect(self._schedule_search)
        fbar.addWidget(self.search_box, 4)

        self.cat_combo = QComboBox()
        self.cat_combo.addItem("All Categories", "")
        self.cat_combo.currentIndexChanged.connect(self._do_search)
        fbar.addWidget(self.cat_combo, 2)

        self.avail_combo = QComboBox()
        self.avail_combo.addItems(["All Availability", "Available", "Unavailable"])
        self.avail_combo.currentIndexChanged.connect(self._do_search)
        fbar.addWidget(self.avail_combo, 2)

        # Search KPI label
        self.kpi_lbl = QLabel("Search: —")
        self.kpi_lbl.setStyleSheet("color:#64748B;font-size:12px;padding-left:8px;")
        fbar.addWidget(self.kpi_lbl)
        root.addLayout(fbar)

        # ── Table ─────────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self._edit_selected)
        root.addWidget(self.table)

        # ── Bottom action bar ─────────────────────────────────────────────────
        bbar = QHBoxLayout(); bbar.setSpacing(10)
        self.count_lbl   = QLabel("0 books")
        self.count_lbl.setStyleSheet("color:#64748B;font-size:12px;")
        bbar.addWidget(self.count_lbl)
        bbar.addStretch()

        self.edit_btn   = QPushButton("Edit Selected");   self.edit_btn.setStyleSheet(_BTN_PRIMARY)
        self.delete_btn = QPushButton("Delete Selected"); self.delete_btn.setStyleSheet(_BTN_DANGER)
        self.defect_btn = QPushButton("Toggle Defect");   self.defect_btn.setStyleSheet(_BTN_WARN)
        bbar.addWidget(self.edit_btn); bbar.addWidget(self.delete_btn); bbar.addWidget(self.defect_btn)
        root.addLayout(bbar)

        # Connections
        self.add_btn.clicked.connect(self._add_book)
        self.edit_btn.clicked.connect(self._edit_selected)
        self.delete_btn.clicked.connect(self._delete_selected)
        self.defect_btn.clicked.connect(self._toggle_defect)
        self.export_btn.clicked.connect(self._export)
        self.refresh_btn.clicked.connect(self.refresh_data)

    # ── Data operations ───────────────────────────────────────────────────────

    def refresh_data(self):
        """Reload categories and full book list."""
        cats = get_book_categories()
        cur = self.cat_combo.currentData()
        self.cat_combo.blockSignals(True)
        self.cat_combo.clear()
        self.cat_combo.addItem("All Categories", "")
        for c in cats:
            self.cat_combo.addItem(c, c)
        idx = self.cat_combo.findData(cur)
        self.cat_combo.setCurrentIndex(max(0, idx))
        self.cat_combo.blockSignals(False)
        self._do_search()

    def _schedule_search(self):
        self._search_timer.start(250)   # debounce 250 ms

    def _do_search(self):
        query    = self.search_box.text().strip()
        category = self.cat_combo.currentData() or ""
        avail_txt = self.avail_combo.currentText()
        availability = "" if avail_txt == "All Availability" else avail_txt

        result = search_books(
            query=query, category=category,
            availability=availability,
            sort_by="title", sort_dir="asc",
            page=1, page_size=500,
        )
        self._books_cache = result["results"]
        self._render_table(self._books_cache)

        ms = result["latency_ms"]
        sla = "OK" if result["sla_ok"] else "BREACH"
        color = "#10B981" if result["sla_ok"] else "#EF4444"
        self.kpi_lbl.setText(f"Search: {ms:.1f}ms ({sla})")
        self.kpi_lbl.setStyleSheet(f"color:{color};font-size:12px;font-weight:600;padding-left:8px;")
        self.count_lbl.setText(f"{result['total']} books")

    def _render_table(self, books: list):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(books))
        GREEN = QColor("#D1FAE5"); RED = QColor("#FEE2E2"); YELLOW = QColor("#FEF9C3")
        for row, b in enumerate(books):
            def _item(text, align=Qt.AlignLeft):
                it = QTableWidgetItem(str(text))
                it.setTextAlignment(align | Qt.AlignVCenter)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                return it

            avail = b["available_copies"]
            total = b["total_copies"]
            self.table.setItem(row, 0, _item(b["id"], Qt.AlignCenter))
            self.table.setItem(row, 1, _item(b["title"]))
            self.table.setItem(row, 2, _item(b["author"]))
            self.table.setItem(row, 3, _item(b["category"]))
            self.table.setItem(row, 4, _item(b["isbn"]))
            self.table.setItem(row, 5, _item(b["year"], Qt.AlignCenter))
            copies_item = _item(f"{avail} / {total}", Qt.AlignCenter)
            if avail == 0:
                copies_item.setBackground(RED)
            elif avail < total:
                copies_item.setBackground(YELLOW)
            else:
                copies_item.setBackground(GREEN)
            self.table.setItem(row, 6, copies_item)
            self.table.setItem(row, 7, _item(b["shelf_location"]))

            if b["defect_flag"]:
                q_item = _item("DEFECT")
                q_item.setForeground(QColor("#EF4444"))
                q_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            else:
                q_item = _item("Inspected OK")
                q_item.setForeground(QColor("#10B981"))
            self.table.setItem(row, 8, q_item)

        self.table.setSortingEnabled(True)

    def _selected_book_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a book row first.")
            return None
        try:
            return int(self.table.item(row, 0).text())
        except Exception:
            return None

    # ── CRUD handlers ─────────────────────────────────────────────────────────

    def _add_book(self):
        dlg = BookDialog(parent=self)
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.get_data()
        ok, book, msg = add_book(
            title=d["title"], author=d["author"], isbn=d["isbn"],
            category=d["category"], year=d["year"],
            total_copies=d["total_copies"], shelf_location=d["shelf_location"],
            processed_by=self.current_user.get("username", "admin"),
        )
        if ok:
            QMessageBox.information(self, "Book Added", msg)
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Error", msg)

    def _edit_selected(self):
        book_id = self._selected_book_id()
        if book_id is None:
            return
        book_data = get_book_by_id(book_id)
        if not book_data:
            QMessageBox.critical(self, "Error", f"Book ID {book_id} not found.")
            return

        dlg = BookDialog(book_data=book_data, parent=self)
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.get_data()
        ok, _, msg = update_book(
            book_id=book_id,
            title=d["title"], author=d["author"], isbn=d["isbn"],
            category=d["category"], year=d["year"],
            total_copies=d["total_copies"], shelf_location=d["shelf_location"],
            defect_flag=d["defect_flag"], defect_notes=d["defect_notes"],
            processed_by=self.current_user.get("username", "admin"),
        )
        if ok:
            QMessageBox.information(self, "Updated", msg)
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Error", msg)

    def _delete_selected(self):
        book_id = self._selected_book_id()
        if book_id is None:
            return
        row = self.table.currentRow()
        title = self.table.item(row, 1).text() if self.table.item(row, 1) else f"Book #{book_id}"
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Permanently delete '{title}' from the catalog?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        ok, msg = delete_book(book_id, processed_by=self.current_user.get("username", "admin"))
        if ok:
            QMessageBox.information(self, "Deleted", msg)
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Cannot Delete", msg)

    def _toggle_defect(self):
        book_id = self._selected_book_id()
        if book_id is None:
            return
        book_data = get_book_by_id(book_id)
        if not book_data:
            return
        new_flag  = not book_data["defect_flag"]
        new_notes = "Flagged during TQM physical inspection" if new_flag else ""
        ok, _, msg = update_book(
            book_id=book_id, defect_flag=new_flag, defect_notes=new_notes,
            processed_by=self.current_user.get("username", "admin"),
        )
        if ok:
            status = "flagged as DEFECTIVE" if new_flag else "cleared (Inspected OK)"
            QMessageBox.information(self, "Quality Status", f"Book #{book_id} {status}.")
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Error", msg)

    def _export(self):
        try:
            path = generate_catalog_excel()
            QMessageBox.information(self, "Export Complete",
                                    f"Catalog exported to Excel successfully:\n\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
