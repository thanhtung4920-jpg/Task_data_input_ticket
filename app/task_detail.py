from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

DETAIL_FIELDS = [
    "Index",
    "TaskID",
    "TaskName",
    "TaskDescription",
    "Activity",
    "ProjectName",
    "USERID",
    "Status",
    "StartDate",
    "FinishedDate",
    "Estimation",
    "Actual",
    "CreatedDate",
    "ModifiedDate",
    "RecordStatus",
]


class TaskDetailView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._value_labels = {}
        layout = QFormLayout()
        for field in DETAIL_FIELDS:
            value_label = QLabel("")
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._value_labels[field] = value_label
            layout.addRow(field, value_label)
        self.setLayout(layout)

    def show_task(self, row):
        for field in DETAIL_FIELDS:
            value = row[field]
            self._value_labels[field].setText("" if value is None else str(value))

    def clear(self):
        for label in self._value_labels.values():
            label.setText("")
