"""
Books View — Interactive Book Catalog Management with Multi-Criteria Filtering.
Demonstrates TQM Principle: Data Accuracy, Defect Tracking & Inventory Control.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QCheckBox,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from app.models.base import get_db
from app.models.book import Book
from app.models.quality_log import QualityLog
from app.ui.components.search_input import SearchInput
from app.ui.components.kpi_badge import KPIBadge
from app.services.report_service import generate_catalog_excel
from app.core.logger import get_logger
import os

logger = get_logger("ui.books")


class AddBookDialog(QDialog):
    """Dialog to create or edit a book in the catalog."""

    def __init__(self, book: Book = None, parent=None):
        super().__init__(parent)
        self.book = book
        self.setWindowTitle("Edit Book" if book else "Add New Book to Catalog")
        self.setFixedWidth(420)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        form = QFormLayout()

        self.title_input = QLineEdit(self.book.title if self.book else "")
        self.author_input = QLineEdit(self.book.author if self.book else "")
        self.isbn_input = QLineEdit(self.book.isbn if self.book else "")
        self.category_input = QLineEdit(self.book.category if self.book else "Computer Science")

        self.total_copies_input = QSpinBox()
        self.total_copies_input.setRange(1, 200)
        self.total_copies_input.setValue(self.book.total_copies if self.book else 5)

        self.defect_check = QCheckBox("Flag for Defect / Maintenance")
        if self.book:
            self.defect_check.setChecked(self.book.defect_flag)

        form.addRow("Book Title *:", self.title_input)
        form.addRow("Author *:", self.author_input)
        form.addRow("ISBN (10/13 digit) *:", self.isbn_input)
        form.addRow("Category *:", self.category_input)
        form.addRow("Total Copies *:", self.total_copies_input)
        form.addRow("", self.defect_check)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Book")
        save_btn.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 6px 14px;")
        save_btn.clicked.connect(self._validate_and_save)

        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def _validate_and_save(self):
        title = self.title_input.text().strip()
        author = self.author_input.text().strip()
        isbn = self.isbn_input.text().strip()
        category = self.category_input.text().strip()
        copies = self.total_copies_input.value()

        if not title or not author or not isbn or not category:
            QMessageBox.warning(self, "Validation Error", "All fields with * are required.")
            return

        with get_db() as db:
            if self.book:
                b = db.get(Book, self.book.id)
                diff = copies - b.total_copies
                b.title = title
                b.author = author
                b.isbn = isbn
                b.category = category
                b.total_copies = copies
                b.available_copies = max(0, b.available_copies + diff)
                b.defect_flag = self.defect_check.isChecked()
                db.add(QualityLog(
                    module="CATALOG",
                    action="BOOK_UPDATED",
                    status="SUCCESS",
                    details=f"Book #{b.id} '{b.title}' updated.",
                ))
            else:
                existing = db.query(Book).filter(Book.isbn == isbn).first()
                if existing:
                    QMessageBox.warning(self, "Duplicate ISBN", f"A book with ISBN {isbn} already exists.")
                    return
                new_book = Book(
                    title=title,
                    author=author,
                    isbn=isbn,
                    category=category,
                    total_copies=copies,
                    available_copies=copies,
                    defect_flag=self.defect_check.isChecked(),
                )
                db.add(new_book)
                db.add(QualityLog(
                    module="CATALOG",
                    action="BOOK_ADDED",
                    status="SUCCESS",
                    details=f"New book '{title}' added to catalog.",
                ))
        self.accept()


class BooksView(QWidget):
    """Catalog table view with search, filter, Excel export, and CRUD controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.load_books()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header with Add Book and Export Buttons
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        t = QLabel("Book Catalog & Inventory")
        t.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A;")
        st = QLabel("Real-time stock tracking, ISBN indexing, and defect monitoring")
        st.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(t)
        title_box.addWidget(st)
        header.addLayout(title_box)
        header.addStretch()

        self.excel_btn = QPushButton("Export to Excel")
        self.excel_btn.setStyleSheet("background-color: #10B981; color: white; font-weight: 600; padding: 8px 14px;")
        self.excel_btn.clicked.connect(self._export_excel)
        header.addWidget(self.excel_btn)

        self.add_btn = QPushButton("+ Add Book")
        self.add_btn.setStyleSheet("background-color: #2563EB; color: white; font-weight: 600; padding: 8px 14px;")
        self.add_btn.clicked.connect(self._add_book)
        header.addWidget(self.add_btn)

        layout.addLayout(header)

        # Filter Controls Bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(12)

        self.search_input = SearchInput("Search by Title, Author, or ISBN...")
        self.search_input.textChanged.connect(self._filter_table)
        filter_bar.addWidget(self.search_input, stretch=3)

        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.currentTextChanged.connect(self._filter_table)
        filter_bar.addWidget(self.category_filter, stretch=1)

        layout.addLayout(filter_bar)

        # Books Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Title", "Author", "ISBN", "Category", "Copies (Avail/Total)", "Quality / Defect", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def load_books(self):
        with get_db() as db:
            self.books = db.query(Book).all()

            # Refresh category dropdown
            categories = sorted(list({b.category for b in self.books}))
            curr = self.category_filter.currentText()
            self.category_filter.blockSignals(True)
            self.category_filter.clear()
            self.category_filter.addItem("All Categories")
            for c in categories:
                self.category_filter.addItem(c)
            idx = self.category_filter.findText(curr)
            if idx >= 0:
                self.category_filter.setCurrentIndex(idx)
            self.category_filter.blockSignals(False)

        self._filter_table()

    def _filter_table(self):
        query = self.search_input.text().strip().lower()
        cat_filter = self.category_filter.currentText()

        filtered = []
        for b in self.books:
            if cat_filter != "All Categories" and b.category != cat_filter:
                continue
            if query and not (query in b.title.lower() or query in b.author.lower() or query in b.isbn.lower()):
                continue
            filtered.append(b)

        self.table.setRowCount(len(filtered))
        for row, b in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(str(b.id)))
            self.table.setItem(row, 1, QTableWidgetItem(b.title))
            self.table.setItem(row, 2, QTableWidgetItem(b.author))
            self.table.setItem(row, 3, QTableWidgetItem(b.isbn))
            self.table.setItem(row, 4, QTableWidgetItem(b.category))

            copies_str = f"{b.available_copies} / {b.total_copies}"
            item_copies = QTableWidgetItem(copies_str)
            item_copies.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, item_copies)

            # Defect badge
            badge = KPIBadge("Defective" if b.defect_flag else "Good Condition",
                             "danger" if b.defect_flag else "success")
            self.table.setCellWidget(row, 6, badge)

            # Action edit button
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("padding: 4px 10px; font-size: 11px;")
            edit_btn.clicked.connect(lambda _, book=b: self._edit_book(book))
            self.table.setCellWidget(row, 7, edit_btn)

    def _add_book(self):
        dlg = AddBookDialog(parent=self)
        if dlg.exec():
            self.load_books()

    def _edit_book(self, book: Book):
        dlg = AddBookDialog(book=book, parent=self)
        if dlg.exec():
            self.load_books()

    def _export_excel(self):
        data = [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "isbn": b.isbn,
                "category": b.category,
                "total_copies": b.total_copies,
                "available_copies": b.available_copies,
                "defect_flag": "Yes" if b.defect_flag else "No",
            }
            for b in self.books
        ]
        try:
            filepath = generate_catalog_excel(data)
            QMessageBox.information(self, "Export Successful", f"Excel report generated successfully:\n\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to generate Excel report: {e}")
