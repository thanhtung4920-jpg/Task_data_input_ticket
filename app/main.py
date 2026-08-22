import sys

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.create_task_form import CreateTaskForm
from app.db import create_task, get_task, init_db, search_tasks, soft_delete_task, update_task
from app.edit_task_form import EditTaskForm
from app.errors import safe_call, safe_get, show_error
from app.master_data import load_master_data
from app.task_detail import TaskDetailView
from app.task_list import TaskListView


class MainWindow(QMainWindow):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.form_container = None

        self.setWindowTitle("Task Tracker")
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.list_page = self._build_list_page()
        self.stack.addWidget(self.list_page)

        self.resize(900, 600)

    def _build_list_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        self.list_view = TaskListView(self._search_fn, delete_fn=self._delete_fn)
        self.detail_view = TaskDetailView()
        self.list_view.task_selected.connect(self.detail_view.show_task)
        self.list_view.table.itemSelectionChanged.connect(self._sync_edit_button)

        self.new_task_button = QPushButton("New Task")
        self.new_task_button.clicked.connect(self._open_create_form)

        self.edit_button = QPushButton("Edit Selected")
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self._open_edit_form)

        top_buttons = QHBoxLayout()
        top_buttons.addWidget(self.new_task_button)
        top_buttons.addWidget(self.edit_button)

        layout.addLayout(top_buttons)
        layout.addWidget(self.list_view)
        layout.addWidget(QLabel("Task Details"))
        layout.addWidget(self.detail_view)
        page.setLayout(layout)
        return page

    def _search_fn(self, task_id, userid, task_name):
        return safe_get(
            lambda: search_tasks(self.conn, task_id=task_id, userid=userid, task_name=task_name),
            default=[],
            parent=self,
            title="Search Error",
        )

    def _delete_fn(self, index):
        result = {}
        if not safe_call(
            lambda: result.update(deleted=soft_delete_task(self.conn, index)),
            parent=self,
            title="Delete Error",
        ):
            return  # safe_call already showed the connectivity error

        if not result["deleted"]:
            show_error(
                self,
                "Delete Error",
                f"Task {index} could not be deleted — it may have already been removed. "
                "The list will refresh to show current data.",
            )

    def _sync_edit_button(self):
        self.edit_button.setEnabled(self.list_view.get_selected_row() is not None)

    def _open_create_form(self):
        master_data = safe_get(load_master_data, parent=self, title="Load Error")
        if master_data is None:
            return

        form = CreateTaskForm(master_data, on_save=self._create_on_save)
        self._show_form_page(form)

    def _create_on_save(self, data):
        create_task(self.conn, data)
        self._return_to_list()

    def _open_edit_form(self):
        task_row = self.list_view.get_selected_row()
        if task_row is None:
            return

        master_data = safe_get(load_master_data, parent=self, title="Load Error")
        if master_data is None:
            return

        form = EditTaskForm(
            master_data,
            task_row,
            on_save=self._edit_on_save,
            on_reload=self._make_reload_fn(task_row["Index"]),
        )
        self._show_form_page(form)

    def _edit_on_save(self, index, loaded_modified_date, data):
        new_modified_date = update_task(self.conn, index, loaded_modified_date, data)
        self._return_to_list()
        return new_modified_date

    def _make_reload_fn(self, index):
        def on_reload():
            result = {}
            if not safe_call(
                lambda: result.update(row=get_task(self.conn, index)),
                parent=self,
                title="Reload Error",
            ):
                return None  # connectivity error already shown

            row = result["row"]
            if row is None or row["RecordStatus"] == "Deleted":
                # this app only ever soft-deletes, so "gone" always means this
                show_error(
                    self,
                    "Reload Error",
                    f"Task {index} no longer exists — it may have been deleted by someone else.",
                )
                return None
            return row

        return on_reload

    def _show_form_page(self, form):
        if self.form_container is not None:
            self.stack.removeWidget(self.form_container)
            self.form_container.deleteLater()

        container = QWidget()
        layout = QVBoxLayout()
        back_button = QPushButton("Cancel / Back to List")
        back_button.clicked.connect(self._return_to_list)
        layout.addWidget(back_button)
        layout.addWidget(form)
        container.setLayout(layout)

        self.form_container = container
        self.stack.addWidget(container)
        self.stack.setCurrentWidget(container)

    def _return_to_list(self):
        self.stack.setCurrentWidget(self.list_page)
        self.list_view.refresh()


def startup():
    """Connect to the DB and load master data. Raises sqlite3.Error or
    MasterDataError on failure; caller is expected to handle those via
    safe_call() rather than let them crash the app."""
    result = {}
    result["conn"] = init_db()
    result["master_data"] = load_master_data()
    return result


def main():
    app = QApplication(sys.argv)

    state = safe_get(startup, title="Startup Error")
    if state is None:
        sys.exit(1)

    window = MainWindow(state["conn"])
    window.show()
    try:
        exit_code = app.exec()
    finally:
        state["conn"].close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
