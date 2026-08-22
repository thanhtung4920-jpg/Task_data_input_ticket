import sqlite3

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

ERROR_STYLE = "border: 1px solid red;"
ERROR_LABEL_STYLE = "color: red; font-size: 11px;"


def make_filter_combo(items):
    combo = QComboBox()
    combo.addItems(items)
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.NoInsert)

    completer = QCompleter(items, combo)
    completer.setCaseSensitivity(Qt.CaseInsensitive)
    completer.setFilterMode(Qt.MatchContains)
    combo.setCompleter(completer)

    return combo


def wrap_with_error(widget):
    error_label = QLabel()
    error_label.setStyleSheet(ERROR_LABEL_STYLE)
    error_label.setVisible(False)

    container = QWidget()
    container_layout = QVBoxLayout()
    container_layout.setContentsMargins(0, 0, 0, 0)
    container_layout.setSpacing(2)
    container_layout.addWidget(widget)
    container_layout.addWidget(error_label)
    container.setLayout(container_layout)

    return container, error_label


class CreateTaskForm(QWidget):
    def __init__(self, master_data, on_save=None, parent=None):
        super().__init__(parent)
        self.master_data = master_data
        self.on_save = on_save

        self.task_id = QLineEdit()
        self.task_name = QLineEdit()
        self.task_description = QPlainTextEdit()

        self.activity = make_filter_combo(master_data["Activity"])
        self.project_name = make_filter_combo(master_data["ProjectName"])
        self.userid = make_filter_combo(master_data["USERID"])
        self.status = make_filter_combo(master_data["Status"])

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())

        self.finished_date = QDateEdit()
        self.finished_date.setCalendarPopup(True)
        self.finished_date.setDate(QDate.currentDate())

        self.estimation = QDoubleSpinBox()
        self.estimation.setRange(0, 100000)
        self.estimation.setSuffix(" h")

        self.actual = QDoubleSpinBox()
        self.actual.setRange(0, 100000)
        self.actual.setSuffix(" h")

        task_name_container, self.task_name_error = wrap_with_error(self.task_name)
        activity_container, self.activity_error = wrap_with_error(self.activity)
        project_name_container, self.project_name_error = wrap_with_error(self.project_name)
        userid_container, self.userid_error = wrap_with_error(self.userid)
        status_container, self.status_error = wrap_with_error(self.status)
        finished_date_container, self.finished_date_error = wrap_with_error(self.finished_date)
        estimation_container, self.estimation_error = wrap_with_error(self.estimation)
        actual_container, self.actual_error = wrap_with_error(self.actual)

        layout = QFormLayout()
        layout.addRow("Task ID", self.task_id)
        layout.addRow("Task Name", task_name_container)
        layout.addRow("Task Description", self.task_description)
        layout.addRow("Activity", activity_container)
        layout.addRow("Project Name", project_name_container)
        layout.addRow("User ID", userid_container)
        layout.addRow("Status", status_container)
        layout.addRow("Start Date", self.start_date)
        layout.addRow("Finished Date", finished_date_container)
        layout.addRow("Estimation", estimation_container)
        layout.addRow("Actual", actual_container)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._handle_save)
        self.status_message = QLabel()
        layout.addRow(self.save_button)
        layout.addRow(self.status_message)

        self.setLayout(layout)

        self._error_fields = {
            "TaskName": (self.task_name, self.task_name_error),
            "Activity": (self.activity, self.activity_error),
            "ProjectName": (self.project_name, self.project_name_error),
            "USERID": (self.userid, self.userid_error),
            "Status": (self.status, self.status_error),
            "FinishedDate": (self.finished_date, self.finished_date_error),
            "Estimation": (self.estimation, self.estimation_error),
            "Actual": (self.actual, self.actual_error),
        }

    def get_form_data(self):
        return {
            "TaskID": self.task_id.text(),
            "TaskName": self.task_name.text(),
            "TaskDescription": self.task_description.toPlainText(),
            "Activity": self.activity.currentText(),
            "ProjectName": self.project_name.currentText(),
            "USERID": self.userid.currentText(),
            "Status": self.status.currentText(),
            "StartDate": self.start_date.date().toString("yyyy-MM-dd"),
            "FinishedDate": self.finished_date.date().toString("yyyy-MM-dd"),
            "Estimation": self.estimation.value(),
            "Actual": self.actual.value(),
        }

    def validate(self):
        errors = {}

        if not self.task_name.text().strip():
            errors["TaskName"] = "Task Name is required."

        for field_name, combo in [
            ("Activity", self.activity),
            ("ProjectName", self.project_name),
            ("USERID", self.userid),
            ("Status", self.status),
        ]:
            if combo.currentText() not in self.master_data[field_name]:
                errors[field_name] = f"{field_name} must be a value from master data."

        if self.finished_date.date() < self.start_date.date():
            errors["FinishedDate"] = "Finished Date must be on or after Start Date."

        if self.estimation.value() < 0:
            errors["Estimation"] = "Estimation must be a non-negative number."

        if self.actual.value() < 0:
            errors["Actual"] = "Actual must be a non-negative number."

        self._apply_errors(errors)
        return errors

    def is_valid(self):
        return not self.validate()

    def _set_status(self, message, is_error=False):
        self.status_message.setStyleSheet(ERROR_LABEL_STYLE if is_error else "")
        self.status_message.setText(message)

    def _handle_save(self):
        if self.validate():
            self._set_status("Please fix the highlighted fields.", is_error=True)
            return

        if self.on_save:
            try:
                self.on_save(self.get_form_data())
            except sqlite3.Error:
                self._set_status(
                    "Could not reach the task database. Check the network connection and try again.",
                    is_error=True,
                )
                return

        self._set_status("Task saved.")

    def _apply_errors(self, errors):
        for field_name, (widget, error_label) in self._error_fields.items():
            if field_name in errors:
                error_label.setText(errors[field_name])
                error_label.setVisible(True)
                widget.setStyleSheet(ERROR_STYLE)
            else:
                error_label.setText("")
                error_label.setVisible(False)
                widget.setStyleSheet("")
