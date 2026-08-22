from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

COLUMNS = [
    "Index",
    "TaskID",
    "TaskName",
    "Activity",
    "ProjectName",
    "USERID",
    "Status",
    "StartDate",
    "FinishedDate",
    "Estimation",
    "Actual",
]


class TaskListView(QWidget):
    task_selected = Signal(object)

    def __init__(self, search_fn, delete_fn=None, parent=None):
        super().__init__(parent)
        self.search_fn = search_fn
        self.delete_fn = delete_fn
        self._rows = []

        self.task_id_filter = QLineEdit()
        self.task_id_filter.setPlaceholderText("Task ID")
        self.userid_filter = QLineEdit()
        self.userid_filter.setPlaceholderText("User ID")
        self.task_name_filter = QLineEdit()
        self.task_name_filter.setPlaceholderText("Task Name")

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.refresh)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_filters)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.task_id_filter)
        filter_layout.addWidget(self.userid_filter)
        filter_layout.addWidget(self.task_name_filter)
        filter_layout.addWidget(self.search_button)
        filter_layout.addWidget(self.clear_button)

        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.itemSelectionChanged.connect(self._handle_selection_changed)

        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._handle_delete)

        layout = QVBoxLayout()
        layout.addLayout(filter_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.delete_button)
        self.setLayout(layout)

        self.refresh()

    def clear_filters(self):
        self.task_id_filter.clear()
        self.userid_filter.clear()
        self.task_name_filter.clear()
        self.refresh()

    def refresh(self):
        rows = self.search_fn(
            self.task_id_filter.text().strip(),
            self.userid_filter.text().strip(),
            self.task_name_filter.text().strip(),
        )

        self._rows = rows
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, column in enumerate(COLUMNS):
                value = row[column]
                self.table.setItem(r, c, QTableWidgetItem("" if value is None else str(value)))

    def get_selected_row(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        row_index = selected[0].row()
        if row_index >= len(self._rows):
            return None
        return self._rows[row_index]

    def _handle_selection_changed(self):
        row = self.get_selected_row()
        self.delete_button.setEnabled(row is not None)
        if row is not None:
            self.task_selected.emit(row)

    def _handle_delete(self):
        row = self.get_selected_row()
        if row is None:
            return

        confirm = QMessageBox.question(
            self,
            "Delete Task",
            f'Delete task "{row["TaskName"]}" (TaskID: {row["TaskID"]})?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        if self.delete_fn:
            self.delete_fn(row["Index"])
        self.refresh()
