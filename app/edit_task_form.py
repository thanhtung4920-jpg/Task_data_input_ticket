import sqlite3

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QLabel, QPushButton

from app.create_task_form import CreateTaskForm
from app.db import OptimisticLockError


class EditTaskForm(CreateTaskForm):
    def __init__(self, master_data, task_row, on_save=None, on_reload=None, parent=None):
        super().__init__(master_data, on_save=on_save, parent=parent)
        self.on_reload = on_reload

        self.save_button.setText("Save Changes")

        self.index = task_row["Index"]
        self.loaded_modified_date = task_row["ModifiedDate"]

        self.index_label = QLabel(str(self.index))
        self.layout().insertRow(0, "Index", self.index_label)

        self.reload_button = QPushButton("Reload Latest Data")
        self.reload_button.setVisible(False)
        self.reload_button.clicked.connect(self._handle_reload)
        self.layout().addRow(self.reload_button)

        self._load_task(task_row)

    def _load_task(self, row):
        self.task_id.setText(row["TaskID"] or "")
        self.task_name.setText(row["TaskName"] or "")
        self.task_description.setPlainText(row["TaskDescription"] or "")
        self.activity.setCurrentText(row["Activity"] or "")
        self.project_name.setCurrentText(row["ProjectName"] or "")
        self.userid.setCurrentText(row["USERID"] or "")
        self.status.setCurrentText(row["Status"] or "")
        self.start_date.setDate(QDate.fromString(row["StartDate"], "yyyy-MM-dd"))
        self.finished_date.setDate(QDate.fromString(row["FinishedDate"], "yyyy-MM-dd"))
        self.estimation.setValue(row["Estimation"] or 0)
        self.actual.setValue(row["Actual"] or 0)

    def _handle_save(self):
        if self.validate():
            self._set_status("Please fix the highlighted fields.", is_error=True)
            return

        if self.on_save:
            try:
                new_modified_date = self.on_save(
                    self.index, self.loaded_modified_date, self.get_form_data()
                )
            except OptimisticLockError:
                self._set_status(
                    "This task was changed by someone else since you loaded it. "
                    "Reload the record and try again.",
                    is_error=True,
                )
                self.save_button.setEnabled(False)
                self.reload_button.setVisible(self.on_reload is not None)
                return
            except sqlite3.Error:
                self._set_status(
                    "Could not reach the task database. Check the network connection and try again.",
                    is_error=True,
                )
                return

            self.loaded_modified_date = new_modified_date

        self._set_status("Task saved.")

    def _handle_reload(self):
        if not self.on_reload:
            return

        fresh_row = self.on_reload()
        if fresh_row is None:
            return  # on_reload's caller is responsible for explaining why

        self.index = fresh_row["Index"]
        self.loaded_modified_date = fresh_row["ModifiedDate"]
        self.index_label.setText(str(self.index))
        self._load_task(fresh_row)
        self._apply_errors({})

        self.save_button.setEnabled(True)
        self.reload_button.setVisible(False)
        self._set_status("Reloaded the latest data. You can edit and save again.")
