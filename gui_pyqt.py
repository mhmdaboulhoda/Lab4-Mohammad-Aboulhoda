import sys
import csv
from db import init_db, save_all, load_all, backup_to

from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QPushButton, QHBoxLayout, QComboBox, QLabel, QTableWidget,
    QTableWidgetItem, QFileDialog, QGridLayout,
    QDialog, QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt

from classes import Student, Instructor, Course
from datastore import save_json, load_json

STUDENTS = []
INSTRUCTORS = []
COURSES = []

def unlink_student_from_everything(s):
    for c in COURSES:
        if s in c.enrolled_students:
            c.enrolled_students.remove(s)
    s.registered_courses.clear()

def unlink_instructor_from_everything(i):
    for c in list(i.assigned_courses):
        c.instructor = None
    i.assigned_courses.clear()

def unlink_course_from_everything(c):
    for s in STUDENTS:
        if c in s.registered_courses:
            s.registered_courses.remove(c)
    if c.instructor:
        if c in c.instructor.assigned_courses:
            c.instructor.assigned_courses.remove(c)
        c.instructor = None

def set_placeholder(line: QLineEdit, text: str):
    line.setPlaceholderText(text)

def combo_values(cb: QComboBox, items):
    cb.blockSignals(True)
    cb.clear()
    cb.addItems(items)
    cb.blockSignals(False)

def student_label(s: Student):
    return f"{s.student_id} | {s.name}"

def instructor_label(i: Instructor):
    return f"{i.instructor_id} | {i.name}"

def course_label(c: Course):
    return f"{c.course_id} | {c.course_name}"

def fill_table(table: QTableWidget, rows, headers):
    table.setRowCount(0)
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setSortingEnabled(False)
    for r, row in enumerate(rows):
        table.insertRow(r)
        for c, val in enumerate(row):
            item = QTableWidgetItem("" if val is None else str(val))
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            table.setItem(r, c, item)
    table.setSortingEnabled(True)
    table.resizeColumnsToContents()

class FilterableTable(QWidget):
    
    def __init__(self, title: str, columns, get_rows, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.get_rows = get_rows

        self.group = QGroupBox(title, self)
        outer = QVBoxLayout(self)
        outer.addWidget(self.group)

        g = QGridLayout(self.group)

        self.filters: list[QLineEdit] = []
        for col, spec in enumerate(columns):
            e = QLineEdit()
            e.setPlaceholderText(spec.get("placeholder", f"search {spec['title'].lower()}"))
            e.textChanged.connect(self.refresh)
            self.filters.append(e)
            g.addWidget(e, 0, col)
        btn_clear = QPushButton("🧹 Clear filters")
        btn_clear.clicked.connect(self.clear_filters)
        g.addWidget(btn_clear, 0, len(columns), alignment=Qt.AlignRight)

       
        self.table = QTableWidget()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c["title"] for c in columns])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultSectionSize(160)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)

        g.addWidget(self.table, 1, 0, 1, len(columns) + 1)

    def clear_filters(self):
        for e in self.filters:
            e.blockSignals(True)
            e.clear()
            e.blockSignals(False)
        self.refresh()

    def _row_matches(self, row_vals):
        for e, val in zip(self.filters, row_vals):
            q = e.text().strip().lower()
            if not q:
                continue
            v = "" if val is None else str(val).lower()
            if q not in v:
                return False
        return True

    def refresh(self):
        rows = [r for r in self.get_rows() if self._row_matches(r)]
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for r_idx, row in enumerate(rows):
            self.table.insertRow(r_idx)
            for c_idx, val in enumerate(row):
                item = QTableWidgetItem("" if val is None else str(val))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(r_idx, c_idx, item)
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()

class StudentEditDialog(QDialog):
    def __init__(self, s: Student, parent=None):
        super().__init__(parent)
        self.s = s
        self.setWindowTitle(f"Edit Student – {s.student_id}")
        form = QFormLayout(self)
        self.e_name = QLineEdit(s.name)
        self.e_age  = QLineEdit(str(s.age))
        self.e_mail = QLineEdit(s.email)
        form.addRow("Name",  self.e_name)
        form.addRow("Age",   self.e_age)
        form.addRow("Email", self.e_mail)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._apply)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _apply(self):
        try:
            self.s.name  = self.e_name.text().strip()
            self.s.age   = int(self.e_age.text().strip())
            self.s.email = self.e_mail.text().strip()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Edit Student", str(e))

class InstructorEditDialog(QDialog):
    def __init__(self, i: Instructor, parent=None):
        super().__init__(parent)
        self.i = i
        self.setWindowTitle(f"Edit Instructor – {i.instructor_id}")
        form = QFormLayout(self)
        self.e_name = QLineEdit(i.name)
        self.e_age  = QLineEdit(str(i.age))
        self.e_mail = QLineEdit(i.email)
        form.addRow("Name",  self.e_name)
        form.addRow("Age",   self.e_age)
        form.addRow("Email", self.e_mail)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._apply)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _apply(self):
        try:
            self.i.name  = self.e_name.text().strip()
            self.i.age   = int(self.e_age.text().strip())
            self.i.email = self.e_mail.text().strip()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Edit Instructor", str(e))

class CourseEditDialog(QDialog):
    def __init__(self, c: Course, parent=None):
        super().__init__(parent)
        self.c = c
        self.setWindowTitle(f"Edit Course – {c.course_id}")
        form = QFormLayout(self)
        self.e_name = QLineEdit(c.course_name)
        form.addRow("Course Name", self.e_name)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._apply)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _apply(self):
        self.c.course_name = self.e_name.text().strip()
        self.accept()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("School Management System (PyQt5)")
        self.resize(980, 820)

        try:
            self.conn = init_db("school.db") 
        except Exception as e:
            self.conn = None
            QMessageBox.critical(self, "Database", f"DB init failed: {e}")

        self.tabs = QTabWidget()
        self.forms_tab = QWidget()
        self.records_tab = QWidget()

        self.tabs.addTab(self.forms_tab, "Forms")
        self.tabs.addTab(self.records_tab, "Records")

        root = QVBoxLayout(self)
        root.addWidget(self.tabs)

        self._build_forms_tab()
        self._build_records_tab()

        
        self.global_refresh()
        
        self.tabs.setCurrentWidget(self.records_tab)

    
    def _build_forms_tab(self):
        lay = QVBoxLayout(self.forms_tab)

        
        gb_student = QGroupBox("Add Student")
        f1 = QFormLayout(gb_student)
        self.s_name = QLineEdit(); set_placeholder(self.s_name, "enter name")
        self.s_age  = QLineEdit(); set_placeholder(self.s_age, "enter age")
        self.s_email= QLineEdit(); set_placeholder(self.s_email, "enter email")
        self.s_id   = QLineEdit(); set_placeholder(self.s_id, "enter student id")
        f1.addRow("Name", self.s_name)
        f1.addRow("Age", self.s_age)
        f1.addRow("Email", self.s_email)
        f1.addRow("Student ID", self.s_id)
        s_add = QPushButton("Add")
        s_add.clicked.connect(self.on_add_student)
        f1.addRow(s_add)
        lay.addWidget(gb_student)

        
        gb_inst = QGroupBox("Add Instructor")
        f2 = QFormLayout(gb_inst)
        self.i_name = QLineEdit(); set_placeholder(self.i_name, "enter name")
        self.i_age  = QLineEdit(); set_placeholder(self.i_age, "enter age")
        self.i_email= QLineEdit(); set_placeholder(self.i_email, "enter email")
        self.i_id   = QLineEdit(); set_placeholder(self.i_id, "enter instructor id")
        f2.addRow("Name", self.i_name)
        f2.addRow("Age", self.i_age)
        f2.addRow("Email", self.i_email)
        f2.addRow("Instructor ID", self.i_id)
        i_add = QPushButton("Add")
        i_add.clicked.connect(self.on_add_instructor)
        f2.addRow(i_add)
        lay.addWidget(gb_inst)

       
        gb_course = QGroupBox("Add Course")
        f3 = QFormLayout(gb_course)
        self.c_id   = QLineEdit(); set_placeholder(self.c_id, "enter course id")
        self.c_name = QLineEdit(); set_placeholder(self.c_name, "enter course name")
        f3.addRow("Course ID", self.c_id)
        f3.addRow("Course Name", self.c_name)
        c_add = QPushButton("Add")
        c_add.clicked.connect(self.on_add_course)
        f3.addRow(c_add)
        lay.addWidget(gb_course)

        
        gb_reg = QGroupBox("Register Student to Course")
        vreg = QVBoxLayout(gb_reg)
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        self.cb_student = QComboBox(); self.cb_student.setEditable(False)
        self.cb_course  = QComboBox(); self.cb_course.setEditable(False)
        self.cb_student.setPlaceholderText("Select student…")
        self.cb_course.setPlaceholderText("Select course…")
        row1.addWidget(QLabel("Student")); row1.addWidget(self.cb_student)
        row2.addWidget(QLabel("Course"));  row2.addWidget(self.cb_course)
        vreg.addLayout(row1); vreg.addLayout(row2)
        btn_reg = QPushButton("Register"); btn_reg.clicked.connect(self.on_register_student)
        vreg.addWidget(btn_reg)
        lay.addWidget(gb_reg)

        
        gb_asg = QGroupBox("Assign Instructor to Course")
        vasg = QVBoxLayout(gb_asg)
        r1 = QHBoxLayout(); r2 = QHBoxLayout()
        self.cb_inst2  = QComboBox(); self.cb_inst2.setEditable(False)
        self.cb_course2= QComboBox(); self.cb_course2.setEditable(False)
        self.cb_inst2.setPlaceholderText("Select instructor…")
        self.cb_course2.setPlaceholderText("Select course…")
        r1.addWidget(QLabel("Instructor")); r1.addWidget(self.cb_inst2)
        r2.addWidget(QLabel("Course"));     r2.addWidget(self.cb_course2)
        vasg.addLayout(r1); vasg.addLayout(r2)
        btn_asg = QPushButton("Assign"); btn_asg.clicked.connect(self.on_assign_instructor)
        vasg.addWidget(btn_asg)
        lay.addWidget(gb_asg)
        lay.addStretch(1)

    
    def _build_records_tab(self):
        lay = QVBoxLayout(self.records_tab)

        row = QHBoxLayout()
        btn_save = QPushButton("Save"); btn_save.clicked.connect(self.on_save)
        btn_load = QPushButton("Load"); btn_load.clicked.connect(self.on_load)
        btn_export = QPushButton("Export CSV"); btn_export.clicked.connect(self.on_export_csv)

        btn_db_save = QPushButton("DB Save"); btn_db_save.clicked.connect(self.on_db_save)
        btn_db_load = QPushButton("DB Load"); btn_db_load.clicked.connect(self.on_db_load)
        btn_db_backup = QPushButton("DB Backup"); btn_db_backup.clicked.connect(self.on_db_backup)

        row.addWidget(btn_save); row.addWidget(btn_load); row.addWidget(btn_export)
        row.addWidget(btn_db_save); row.addWidget(btn_db_load); row.addWidget(btn_db_backup)
        row.addStretch(1)
        lay.addLayout(row)

        self.tbl_students = FilterableTable(
            title="Students",
            columns=[
                {"title": "Student ID",         "placeholder": "search by Student ID"},
                {"title": "Name",               "placeholder": "search by Name"},
                {"title": "Age",                "placeholder": "search by Age"},
                {"title": "Email",              "placeholder": "search by Email"},
                {"title": "Registered Courses", "placeholder": "search by Course"},
            ],
            get_rows=lambda: [
                (
                    s.student_id,
                    s.name,
                    s.age,
                    s.email,
                    ", ".join(f"{c.course_name} {c.course_id}" for c in s.registered_courses),
                ) for s in STUDENTS
            ],
            parent=self.records_tab,
        )
        lay.addWidget(self.tbl_students)

        row_stu = QHBoxLayout()
        btn_stu_edit = QPushButton("Edit")
        btn_stu_del  = QPushButton("Delete")
        row_stu.addWidget(btn_stu_edit)
        row_stu.addWidget(btn_stu_del)
        row_stu.addStretch(1)
        lay.addLayout(row_stu)

        def _selected_student():
            idxs = self.tbl_students.table.selectionModel().selectedRows()
            if not idxs:
                return None
            r = idxs[0].row()
            sid = self.tbl_students.table.item(r, 0).text()
            for s in STUDENTS:
                if s.student_id == sid:
                    return s
            return None

        def on_edit_student():
            s = _selected_student()
            if not s:
                QMessageBox.information(self, "Edit Student", "Select a student row first.")
                return
            dlg = StudentEditDialog(s, self)
            if dlg.exec_():
                self.global_refresh()

        def on_delete_student():
            s = _selected_student()
            if not s:
                QMessageBox.information(self, "Delete Student", "Select a student row first.")
                return
            confirm = QMessageBox.question(
                self, "Delete Student", f"Delete {s.name} ({s.student_id})?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                unlink_student_from_everything(s)
                STUDENTS.remove(s)
                self.global_refresh()

        btn_stu_edit.clicked.connect(on_edit_student)
        btn_stu_del.clicked.connect(on_delete_student)

        self.tbl_instructors = FilterableTable(
            title="Instructors",
            columns=[
                {"title": "Instructor ID",     "placeholder": "search by Instructor ID"},
                {"title": "Name",              "placeholder": "search by Name"},
                {"title": "Age",               "placeholder": "search by Age"},
                {"title": "Email",             "placeholder": "search by Email"},
                {"title": "Assigned Courses",  "placeholder": "search by Course"},
            ],
            get_rows=lambda: [
                (
                    i.instructor_id,
                    i.name,
                    i.age,
                    i.email,
                    ", ".join(f"{c.course_name} {c.course_id}" for c in i.assigned_courses),
                ) for i in INSTRUCTORS
            ],
            parent=self.records_tab,
        )
        lay.addWidget(self.tbl_instructors)

        row_ins = QHBoxLayout()
        btn_ins_edit = QPushButton("Edit")
        btn_ins_del  = QPushButton("Delete")
        row_ins.addWidget(btn_ins_edit)
        row_ins.addWidget(btn_ins_del)
        row_ins.addStretch(1)
        lay.addLayout(row_ins)

        def _selected_instructor():
            idxs = self.tbl_instructors.table.selectionModel().selectedRows()
            if not idxs:
                return None
            r = idxs[0].row()
            iid = self.tbl_instructors.table.item(r, 0).text()
            for i in INSTRUCTORS:
                if i.instructor_id == iid:
                    return i
            return None

        def on_edit_instructor():
            i = _selected_instructor()
            if not i:
                QMessageBox.information(self, "Edit Instructor", "Select an instructor row first.")
                return
            dlg = InstructorEditDialog(i, self)
            if dlg.exec_():
                self.global_refresh()

        def on_delete_instructor():
            i = _selected_instructor()
            if not i:
                QMessageBox.information(self, "Delete Instructor", "Select an instructor row first.")
                return
            confirm = QMessageBox.question(
                self, "Delete Instructor", f"Delete {i.name} ({i.instructor_id})?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                unlink_instructor_from_everything(i)
                INSTRUCTORS.remove(i)
                self.global_refresh()

        btn_ins_edit.clicked.connect(on_edit_instructor)
        btn_ins_del.clicked.connect(on_delete_instructor)

        self.tbl_courses = FilterableTable(
            title="Courses",
            columns=[
                {"title": "Course ID",         "placeholder": "search by Course ID"},
                {"title": "Course Name",       "placeholder": "search by Name"},
                {"title": "Instructor",        "placeholder": "search by Instructor"},
                {"title": "Enrolled Students", "placeholder": "search by Student"},
            ],
            get_rows=lambda: [
                (
                    c.course_id,
                    c.course_name,
                    c.instructor.name if c.instructor else "",
                    ", ".join(f"{s.student_id}-{s.name}" for s in c.enrolled_students),
                ) for c in COURSES
            ],
            parent=self.records_tab,
        )
        lay.addWidget(self.tbl_courses)

        row_crs = QHBoxLayout()
        btn_crs_edit = QPushButton("Edit")
        btn_crs_del  = QPushButton("Delete")
        row_crs.addWidget(btn_crs_edit)
        row_crs.addWidget(btn_crs_del)
        row_crs.addStretch(1)
        lay.addLayout(row_crs)

        def _selected_course():
            idxs = self.tbl_courses.table.selectionModel().selectedRows()
            if not idxs:
                return None
            r = idxs[0].row()
            cid = self.tbl_courses.table.item(r, 0).text()
            for c in COURSES:
                if c.course_id == cid:
                    return c
            return None

        def on_edit_course():
            c = _selected_course()
            if not c:
                QMessageBox.information(self, "Edit Course", "Select a course row first.")
                return
            dlg = CourseEditDialog(c, self)
            if dlg.exec_():
                self.global_refresh()

        def on_delete_course():
            c = _selected_course()
            if not c:
                QMessageBox.information(self, "Delete Course", "Select a course row first.")
                return
            confirm = QMessageBox.question(
                self, "Delete Course", f"Delete {c.course_name} ({c.course_id})?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                unlink_course_from_everything(c)
                COURSES.remove(c)
                self.global_refresh()

        btn_crs_edit.clicked.connect(on_edit_course)
        btn_crs_del.clicked.connect(on_delete_course)

    def on_add_student(self):
        try:
            s = Student(self.s_name.text().strip(),
                        int(self.s_age.text().strip()),
                        self.s_email.text().strip(),
                        self.s_id.text().strip())
            STUDENTS.append(s)
            self.s_name.clear(); self.s_age.clear(); self.s_email.clear(); self.s_id.clear()
            self.global_refresh()
        except Exception as e:
            self._error(f"Add Student: {e}")

    def on_add_instructor(self):
        try:
            i = Instructor(self.i_name.text().strip(),
                           int(self.i_age.text().strip()),
                           self.i_email.text().strip(),
                           self.i_id.text().strip())
            INSTRUCTORS.append(i)
            self.i_name.clear(); self.i_age.clear(); self.i_email.clear(); self.i_id.clear()
            self.global_refresh()
        except Exception as e:
            self._error(f"Add Instructor: {e}")

    def on_add_course(self):
        try:
            c = Course(self.c_id.text().strip(), self.c_name.text().strip(), None)
            COURSES.append(c)
            self.c_id.clear(); self.c_name.clear()
            self.global_refresh()
        except Exception as e:
            self._error(f"Add Course: {e}")

    def on_register_student(self):
        s_idx = self.cb_student.currentIndex()
        c_idx = self.cb_course.currentIndex()
        if s_idx < 0 or c_idx < 0:
            QMessageBox.information(self, "Register", "Select both a student and a course.")
            return

        s = STUDENTS[s_idx]
        c = COURSES[c_idx]

        if not hasattr(s, "registered_courses") or s.registered_courses is None:
            s.registered_courses = []
        if not hasattr(c, "enrolled_students") or c.enrolled_students is None:
            c.enrolled_students = []

        if (c in s.registered_courses) or (s in c.enrolled_students):
            QMessageBox.information(self, "Register", f"{s.name} is already registered in {c.course_name} ({c.course_id}).")
            return

        s.registered_courses.append(c)
        c.enrolled_students.append(s)

        self.global_refresh()
        QMessageBox.information(self, "Register", f"Registered {s.name} → {c.course_name} ({c.course_id}).")

    def on_assign_instructor(self):
        i_idx = self.cb_inst2.currentIndex()
        c_idx = self.cb_course2.currentIndex()
        if i_idx < 0 or c_idx < 0:
            self._error("Select both an instructor and a course.")
            return
        ins = INSTRUCTORS[i_idx]; c = COURSES[c_idx]
        try:
            ins.assign_course(c)
        except Exception as e:
            self._error(str(e)); return
        self.global_refresh()

    def on_save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save data", "", "JSON (*.json)")
        if not path:
            return
        save_json(path, STUDENTS, INSTRUCTORS, COURSES)

    def on_load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load data", "", "JSON (*.json)")
        if not path:
            return
        students, instructors, courses = load_json(path)
        STUDENTS[:] = students
        INSTRUCTORS[:] = instructors
        COURSES[:] = courses
        self.global_refresh()

    def on_export_csv(self):
        directory = QFileDialog.getExistingDirectory(self, "Choose folder to save CSV files")
        if not directory:
            return

        stu_path = f"{directory}/students.csv"
        with open(stu_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["student_id", "name", "age", "email", "registered_course_ids"])
            for s in STUDENTS:
                course_ids = ";".join(c.course_id for c in getattr(s, "registered_courses", []))
                w.writerow([s.student_id, s.name, s.age, s.email, course_ids])

        inst_path = f"{directory}/instructors.csv"
        with open(inst_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["instructor_id", "name", "age", "email", "assigned_course_ids"])
            for i in INSTRUCTORS:
                course_ids = ";".join(c.course_id for c in getattr(i, "assigned_courses", []))
                w.writerow([i.instructor_id, i.name, i.age, i.email, course_ids])

        crs_path = f"{directory}/courses.csv"
        with open(crs_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["course_id", "course_name", "instructor_id", "enrolled_student_ids"])
            for c in COURSES:
                instr_id = c.instructor.instructor_id if c.instructor else ""
                stu_ids = ";".join(s.student_id for s in getattr(c, "enrolled_students", []))
                w.writerow([c.course_id, c.course_name, instr_id, stu_ids])

        QMessageBox.information(self, "Export Complete", f"Exported:\n- {stu_path}\n- {inst_path}\n- {crs_path}")

    def on_db_save(self):
        if not self.conn:
            QMessageBox.critical(self, "Database", "No DB connection.")
            return
        try:
            save_all(self.conn, STUDENTS, INSTRUCTORS, COURSES)
            QMessageBox.information(self, "Database", "Saved to SQLite database (school.db).")
        except Exception as e:
            QMessageBox.critical(self, "Database Save", str(e))

    def on_db_load(self):
        if not self.conn:
            QMessageBox.critical(self, "Database", "No DB connection.")
            return
        try:
            students, instructors, courses = load_all(self.conn)
            STUDENTS[:] = students
            INSTRUCTORS[:] = instructors
            COURSES[:] = courses
            self.global_refresh()
            QMessageBox.information(self, "Database", "Loaded from SQLite database (school.db).")
        except Exception as e:
            QMessageBox.critical(self, "Database Load", str(e))

    def on_db_backup(self):
        if not self.conn:
            QMessageBox.critical(self, "Database", "No DB connection.")
            return
        try:
            path, _ = QFileDialog.getSaveFileName(self, "Backup database to…", "school-backup.db", "DB (*.db)")
            if not path:
                return
            backup_to(self.conn, path)
            QMessageBox.information(self, "Database", f"Backup written to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Database Backup", str(e))

    def global_refresh(self):
        combo_values(self.cb_student, [f"{s.student_id} | {s.name}" for s in STUDENTS])
        combo_values(self.cb_course,  [f"{c.course_id} | {c.course_name}" for c in COURSES])
        combo_values(self.cb_inst2,   [f"{i.instructor_id} | {i.name}" for i in INSTRUCTORS])
        combo_values(self.cb_course2, [f"{c.course_id} | {c.course_name}" for c in COURSES])

        self.tbl_students.refresh()
        self.tbl_instructors.refresh()
        self.tbl_courses.refresh()

    def _error(self, msg):
        print("ERROR:", msg)

    def closeEvent(self, event):
        try:
            if getattr(self, "conn", None):
                self.conn.close()
        except Exception:
            pass
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
