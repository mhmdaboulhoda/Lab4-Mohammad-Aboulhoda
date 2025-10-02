import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.filedialog as fd
from classes import Student, Instructor, Course
from datastore import save_json, load_json
from db import init_db, save_all, load_all, backup_to  

STUDENTS = []
INSTRUCTORS = []
COURSES = []

DB_CONN = None

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

def add_placeholder(entry: ttk.Entry, text: str):
    entry.delete(0, "end")
    entry.insert(0, text)
    entry.configure(foreground="#888")

    def _on_focus_in(_):
        if entry.get() == text:
            entry.delete(0, "end")
            entry.configure(foreground="#000")

    def _on_focus_out(_):
        if entry.get().strip() == "":
            entry.delete(0, "end")
            entry.insert(0, text)
            entry.configure(foreground="#888")

    entry.bind("<FocusIn>", _on_focus_in)
    entry.bind("<FocusOut>", _on_focus_out)

def set_combo_placeholder(cb: ttk.Combobox, text: str):
    cb.set(text)

    try:
        cb.configure(foreground="#888")
    except Exception:
        pass

    def _on_select(_):
        try:
            cb.configure(foreground="#000")
        except Exception:
            pass

    cb.bind("<<ComboboxSelected>>", _on_select)

class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)

        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=vbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        def _resize(e):
            self.canvas.itemconfigure(window_id, width=e.width)
        self.canvas.bind("<Configure>", _resize)

        def _wheel(event):
            if hasattr(event, "delta") and event.delta:
                self.canvas.yview_scroll(int(-event.delta/120), "units")   
            else:
                
                if getattr(event, "num", None) == 4:
                    self.canvas.yview_scroll(-3, "units")
                elif getattr(event, "num", None) == 5:
                    self.canvas.yview_scroll(3, "units")
        self.bind_all("<MouseWheel>", _wheel)
        self.bind_all("<Button-4>", _wheel)
        self.bind_all("<Button-5>", _wheel)



def build_student_form(parent, on_changed=None):
    frame = ttk.LabelFrame(parent, text="Add Student", padding=6)

    ttk.Label(frame, text="Name").grid(row=0, column=0, sticky="w", pady=2, padx=(2,6))
    e_name = ttk.Entry(frame, width=34); e_name.grid(row=0, column=1, sticky="w", pady=2)

    ttk.Label(frame, text="Age").grid(row=1, column=0, sticky="w", pady=2, padx=(2,6))
    e_age = ttk.Entry(frame, width=12); e_age.grid(row=1, column=1, sticky="w", pady=2)

    ttk.Label(frame, text="Email").grid(row=2, column=0, sticky="w", pady=2, padx=(2,6))
    e_email = ttk.Entry(frame, width=34); e_email.grid(row=2, column=1, sticky="w", pady=2)

    ttk.Label(frame, text="Student ID").grid(row=3, column=0, sticky="w", pady=2, padx=(2,6))
    e_sid = ttk.Entry(frame, width=20); e_sid.grid(row=3, column=1, sticky="w", pady=2)

    add_placeholder(e_name, "enter name")
    add_placeholder(e_age, "enter age")
    add_placeholder(e_email, "enter email")
    add_placeholder(e_sid, "enter student id")

    status = ttk.Label(frame, text="", foreground="gray")
    status.grid(row=5, column=0, columnspan=2, sticky="w", pady=(2,0))

    def on_add():
        try:
            name  = "" if e_name.cget("foreground") == "#888" else e_name.get()
            age_s = "" if e_age.cget("foreground")  == "#888" else e_age.get()
            email = "" if e_email.cget("foreground")== "#888" else e_email.get()
            sid   = "" if e_sid.cget("foreground")  == "#888" else e_sid.get()

            s = Student(name, int(age_s), email, sid)
            STUDENTS.append(s)

            for w, ph in ((e_name,"enter name"), (e_age,"enter age"),
                          (e_email,"enter email"), (e_sid,"enter student id")):
                add_placeholder(w, ph)

            status.config(text=f"Added student: {s.name} ({s.student_id})")
            if on_changed: on_changed()
        except Exception as ex:
            messagebox.showerror("Add Student", str(ex))

    ttk.Button(frame, text="Add", command=on_add).grid(row=4, column=0, columnspan=2, pady=4)
    return frame



def build_instructor_form(parent, on_changed=None):
    frame = ttk.LabelFrame(parent, text="Add Instructor", padding=6)

    ttk.Label(frame, text="Name").grid(row=0, column=0, sticky="w", pady=2, padx=(2,6))
    e_name = ttk.Entry(frame, width=34); e_name.grid(row=0, column=1, sticky="w", pady=2)

    ttk.Label(frame, text="Age").grid(row=1, column=0, sticky="w", pady=2, padx=(2,6))
    e_age = ttk.Entry(frame, width=12); e_age.grid(row=1, column=1, sticky="w", pady=2)

    ttk.Label(frame, text="Email").grid(row=2, column=0, sticky="w", pady=2, padx=(2,6))
    e_email = ttk.Entry(frame, width=34); e_email.grid(row=2, column=1, sticky="w", pady=2)

    ttk.Label(frame, text="Instructor ID").grid(row=3, column=0, sticky="w", pady=2, padx=(2,6))
    e_iid = ttk.Entry(frame, width=20); e_iid.grid(row=3, column=1, sticky="w", pady=2)

    add_placeholder(e_name, "enter name")
    add_placeholder(e_age, "enter age")
    add_placeholder(e_email, "enter email")
    add_placeholder(e_iid, "enter instructor id")

    status = ttk.Label(frame, text="", foreground="gray")
    status.grid(row=5, column=0, columnspan=2, sticky="w", pady=(2,0))

    def on_add():
        try:
            name  = "" if e_name.cget("foreground") == "#888" else e_name.get()
            age_s = "" if e_age.cget("foreground")  == "#888" else e_age.get()
            email = "" if e_email.cget("foreground")== "#888" else e_email.get()
            iid   = "" if e_iid.cget("foreground")  == "#888" else e_iid.get()

            i = Instructor(name, int(age_s), email, iid)
            INSTRUCTORS.append(i)

            for w, ph in ((e_name,"enter name"), (e_age,"enter age"),
                          (e_email,"enter email"), (e_iid,"enter instructor id")):
                add_placeholder(w, ph)

            status.config(text=f"Added instructor: {i.name} ({i.instructor_id})")
            if on_changed: on_changed()
        except Exception as ex:
            messagebox.showerror("Add Instructor", str(ex))

    ttk.Button(frame, text="Add", command=on_add).grid(row=4, column=0, columnspan=2, pady=4)
    return frame


def build_course_form(parent, on_changed=None):
    frame = ttk.LabelFrame(parent, text="Add Course", padding=6)

    ttk.Label(frame, text="Course ID").grid(row=0, column=0, sticky="w", pady=2, padx=(2,6))
    e_cid = ttk.Entry(frame, width=20); e_cid.grid(row=0, column=1, sticky="w", pady=2)

    ttk.Label(frame, text="Course Name").grid(row=1, column=0, sticky="w", pady=2, padx=(2,6))
    e_cname = ttk.Entry(frame, width=34); e_cname.grid(row=1, column=1, sticky="w", pady=2)

    add_placeholder(e_cid, "enter course id")
    add_placeholder(e_cname, "enter course name")

    status = ttk.Label(frame, text="", foreground="gray")
    status.grid(row=3, column=0, columnspan=2, sticky="w", pady=(2,0))

    def on_add():
        try:
            cid   = "" if e_cid.cget("foreground")   == "#888" else e_cid.get()
            cname = "" if e_cname.cget("foreground") == "#888" else e_cname.get()

            c = Course(cid, cname, None)
            COURSES.append(c)

            for w, ph in ((e_cid,"enter course id"), (e_cname,"enter course name")):
                add_placeholder(w, ph)

            status.config(text=f"Added course: {c.course_name} ({c.course_id})")
            if on_changed: on_changed()
        except Exception as ex:
            messagebox.showerror("Add Course", str(ex))

    ttk.Button(frame, text="Add", command=on_add).grid(row=2, column=0, columnspan=2, pady=4)
    return frame


def build_registration_form(parent, on_refresh):
    frame = ttk.LabelFrame(parent, text="Register Student to Course", padding=10)
    frame.columnconfigure(1, weight=1)

    ttk.Label(frame, text="Student").grid(row=0, column=0, sticky="w", pady=4)
    cb_student = ttk.Combobox(frame, state="readonly"); cb_student.grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(frame, text="Course").grid(row=1, column=0, sticky="w", pady=4)
    cb_course = ttk.Combobox(frame, state="readonly"); cb_course.grid(row=1, column=1, sticky="ew", pady=4)

    set_combo_placeholder(cb_student, "Select student…")
    set_combo_placeholder(cb_course,  "Select course…")

    status = ttk.Label(frame, text="", foreground="gray")
    status.grid(row=3, column=0, columnspan=2, sticky="w", pady=2)

    def refresh_options():
        cb_student["values"] = [f"{s.student_id} | {s.name}" for s in STUDENTS]
        cb_course["values"]  = [f"{c.course_id} | {c.course_name}" for c in COURSES]

    def on_register():
        try:
            s_idx = cb_student.current()
            c_idx = cb_course.current()
            if s_idx < 0 or c_idx < 0:
                raise ValueError("Select both a student and a course.")
            s = STUDENTS[s_idx]
            c = COURSES[c_idx]
            msg = s.register(c) 
            status.config(text=msg)
            on_refresh()
        except Exception as ex:
            messagebox.showerror("Register Student", str(ex))

    ttk.Button(frame, text="Register", command=on_register)\
       .grid(row=2, column=0, columnspan=2, pady=8)

    refresh_options()
    frame.refresh_options = refresh_options
    return frame

def build_assignment_form(parent, on_refresh):
    frame = ttk.LabelFrame(parent, text="Assign Instructor to Course", padding=10)
    frame.columnconfigure(1, weight=1)

    ttk.Label(frame, text="Instructor").grid(row=0, column=0, sticky="w", pady=4)
    cb_inst = ttk.Combobox(frame, state="readonly"); cb_inst.grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(frame, text="Course").grid(row=1, column=0, sticky="w", pady=4)
    cb_course = ttk.Combobox(frame, state="readonly"); cb_course.grid(row=1, column=1, sticky="ew", pady=4)

    set_combo_placeholder(cb_inst,   "Select instructor…")
    set_combo_placeholder(cb_course, "Select course…")

    status = ttk.Label(frame, text="", foreground="gray")
    status.grid(row=3, column=0, columnspan=2, sticky="w", pady=2)

    def refresh_options():
        cb_inst["values"]   = [f"{i.instructor_id} | {i.name}" for i in INSTRUCTORS]
        cb_course["values"] = [f"{c.course_id} | {c.course_name}" for c in COURSES]

    def on_assign():
        try:
            i_idx = cb_inst.current()
            c_idx = cb_course.current()
            if i_idx < 0 or c_idx < 0:
                raise ValueError("Select both an instructor and a course.")
            ins = INSTRUCTORS[i_idx]
            c = COURSES[c_idx]
            msg = ins.assign_course(c) 
            status.config(text=msg)
            on_refresh()
        except Exception as ex:
            messagebox.showerror("Assign Instructor", str(ex))

    ttk.Button(frame, text="Assign", command=on_assign)\
       .grid(row=2, column=0, columnspan=2, pady=8)

    refresh_options()
    frame.refresh_options = refresh_options
    return frame

def edit_dialog_student(parent, s, on_ok):
    win = tk.Toplevel(parent)
    win.title(f"Edit Student – {s.student_id}")
    win.grab_set()

    tk.Label(win, text="Name").grid(row=0, column=0, sticky="e", padx=6, pady=4)
    e_name = ttk.Entry(win)
    e_name.insert(0, s.name)
    e_name.grid(row=0, column=1, padx=6, pady=4)

    tk.Label(win, text="Age").grid(row=1, column=0, sticky="e", padx=6, pady=4)
    e_age = ttk.Entry(win)
    e_age.insert(0, str(s.age))
    e_age.grid(row=1, column=1, padx=6, pady=4)

    tk.Label(win, text="Email").grid(row=2, column=0, sticky="e", padx=6, pady=4)
    e_email = ttk.Entry(win)
    e_email.insert(0, s.email)
    e_email.grid(row=2, column=1, padx=6, pady=4)

    def ok():
        try:
            s.name = e_name.get().strip()
            s.age = int(e_age.get().strip())
            s.email = e_email.get().strip()
            on_ok()
            win.destroy()
        except Exception as ex:
            messagebox.showerror("Edit Student", str(ex), parent=win)

    ttk.Button(win, text="OK", command=ok).grid(row=3, column=0, padx=6, pady=8)
    ttk.Button(win, text="Cancel", command=win.destroy).grid(row=3, column=1, padx=6, pady=8)


def edit_dialog_instructor(parent, i, on_ok):
    win = tk.Toplevel(parent)
    win.title(f"Edit Instructor – {i.instructor_id}")
    win.grab_set()

    tk.Label(win, text="Name").grid(row=0, column=0, sticky="e", padx=6, pady=4)
    e_name = ttk.Entry(win)
    e_name.insert(0, i.name)
    e_name.grid(row=0, column=1, padx=6, pady=4)

    tk.Label(win, text="Age").grid(row=1, column=0, sticky="e", padx=6, pady=4)
    e_age = ttk.Entry(win)
    e_age.insert(0, str(i.age))
    e_age.grid(row=1, column=1, padx=6, pady=4)

    tk.Label(win, text="Email").grid(row=2, column=0, sticky="e", padx=6, pady=4)
    e_email = ttk.Entry(win)
    e_email.insert(0, i.email)
    e_email.grid(row=2, column=1, padx=6, pady=4)

    def ok():
        try:
            i.name = e_name.get().strip()
            i.age = int(e_age.get().strip())
            i.email = e_email.get().strip()
            on_ok()
            win.destroy()
        except Exception as ex:
            messagebox.showerror("Edit Instructor", str(ex), parent=win)

    ttk.Button(win, text="OK", command=ok).grid(row=3, column=0, padx=6, pady=8)
    ttk.Button(win, text="Cancel", command=win.destroy).grid(row=3, column=1, padx=6, pady=8)


def edit_dialog_course(parent, c, on_ok):
    win = tk.Toplevel(parent)
    win.title(f"Edit Course – {c.course_id}")
    win.grab_set()

    tk.Label(win, text="Course Name").grid(row=0, column=0, sticky="e", padx=6, pady=4)
    e_name = ttk.Entry(win)
    e_name.insert(0, c.course_name)
    e_name.grid(row=0, column=1, padx=6, pady=4)

    def ok():
        c.course_name = e_name.get().strip()
        on_ok()
        win.destroy()

    ttk.Button(win, text="OK", command=ok).grid(row=1, column=0, padx=6, pady=8)
    ttk.Button(win, text="Cancel", command=win.destroy).grid(row=1, column=1, padx=6, pady=8)


def build_tables_and_search(parent):
    class FilterableTable:
        PIX_PER_CHAR = 8

        def __init__(self, parent, title, columns, get_rows):
            self.frame = ttk.LabelFrame(parent, text=title, padding=8)
            self.get_rows = get_rows
            self.columns = columns

            # filter row
            self.filter_row = ttk.Frame(self.frame)
            self.filter_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
            for j, (_, _, width, _, _) in enumerate(columns):
                self.filter_row.grid_columnconfigure(j, minsize=width, weight=1)
            self.filter_row.grid_columnconfigure(len(columns), weight=1)

            # table
            self.tv = ttk.Treeview(
                self.frame,
                columns=[k for k, *_ in columns],
                show="headings",
                height=6
            )
            self.tv.grid(row=1, column=0, sticky="nsew")
            self.frame.columnconfigure(0, weight=1)
            self.frame.rowconfigure(1, weight=1)

            vs = ttk.Scrollbar(self.frame, orient="vertical", command=self.tv.yview)
            self.tv.configure(yscrollcommand=vs.set)
            vs.grid(row=1, column=1, sticky="ns")

            # columns + filters
            self.filters = []
            for col_idx, (key, heading, width, anchor, ph_text) in enumerate(columns):
                self.tv.heading(key, text=heading)
                self.tv.column(key, width=width, anchor=anchor)

                ent_chars = max(10, width // self.PIX_PER_CHAR)
                e = ttk.Entry(self.filter_row, width=ent_chars)
                e.grid(row=0, column=col_idx, padx=(0, 6), sticky="ew")

                def _add_placeholder(entry, text):
                    entry.delete(0, "end"); entry.insert(0, text); entry.configure(foreground="#888")
                    def _in(_):  # focus in
                        if entry.get() == text:
                            entry.delete(0, "end"); entry.configure(foreground="#000")
                    def _out(_):  # focus out
                        if entry.get().strip() == "":
                            entry.delete(0, "end"); entry.insert(0, text); entry.configure(foreground="#888")
                    entry.bind("<FocusIn>", _in); entry.bind("<FocusOut>", _out)

                _add_placeholder(e, ph_text)
                e.bind("<KeyRelease>", lambda *_: self.refresh())
                self.filters.append((e, ph_text))

            self.clear_btn = ttk.Button(self.filter_row, text="🧹 Clear filters", command=self.clear_filters)
            self.clear_btn.grid(row=0, column=len(columns)+1, sticky="e")

            # action bar
            bar = ttk.Frame(self.frame)
            bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6,0))
            self.btn_edit = ttk.Button(bar, text="Edit")
            self.btn_del  = ttk.Button(bar, text="Delete")
            self.btn_edit.pack(side="left")
            self.btn_del.pack(side="left", padx=6)

        def _match_row(self, values):
            for idx, (entry, ph_text) in enumerate(self.filters):
                q = entry.get().strip().lower()
                if q == ph_text.lower():
                    q = ""
                if not q:
                    continue
                v = "" if values[idx] is None else str(values[idx]).lower()
                if q not in v:
                    return False
            return True

        def clear_filters(self):
            for entry, ph_text in self.filters:
                entry.delete(0, "end")
                entry.insert(0, ph_text)
                entry.configure(foreground="#888")
            self.refresh()

        def refresh(self):
            for iid in self.tv.get_children():
                self.tv.delete(iid)
            for row in self.get_rows():
                if self._match_row(row):
                    self.tv.insert("", "end", values=row)

    
    outer = ttk.Frame(parent, padding=8)
    outer.columnconfigure(0, weight=1)
    outer.rowconfigure(0, weight=1)
    outer.rowconfigure(1, weight=1)
    outer.rowconfigure(2, weight=2)

    students_tbl = FilterableTable(
        outer, "Students",
        columns=[
            ("id",      "Student ID",          150, "w", "search by Student ID"),
            ("name",    "Name",                180, "w", "search by Name"),
            ("age",     "Age",                  90, "w", "search by Age"),
            ("email",   "Email",               260, "w", "search by Email"),
            ("courses", "Registered Courses",  300, "w", "search by Course"),
        ],
        get_rows=lambda: [
            (s.student_id, s.name, s.age, s.email,
             ", ".join(f"{c.course_name} {c.course_id}" for c in s.registered_courses))
            for s in STUDENTS
        ],
    )
    students_tbl.frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

    def student_selected():
        sel = students_tbl.tv.selection()
        if not sel: return None
        sid = students_tbl.tv.item(sel[0], "values")[0]
        for s in STUDENTS:
            if s.student_id == sid:
                return s
        return None

    def on_edit_student():
        s = student_selected()
        if not s:
            messagebox.showinfo("Edit Student", "Select a student row first."); return
        edit_dialog_student(outer, s, on_ok=lambda: refresh_tables())

    def on_del_student():
        s = student_selected()
        if not s:
            messagebox.showinfo("Delete Student", "Select a student row first."); return
        if not messagebox.askyesno("Delete Student", f"Delete {s.name} ({s.student_id})?"):
            return
        unlink_student_from_everything(s)
        STUDENTS.remove(s)
        refresh_tables()

    students_tbl.btn_edit.config(command=on_edit_student)
    students_tbl.btn_del.config(command=on_del_student)

    instructors_tbl = FilterableTable(
        outer, "Instructors",
        columns=[
            ("id",      "Instructor ID",      150, "w", "search by Instructor ID"),
            ("name",    "Name",               180, "w", "search by Name"),
            ("age",     "Age",                 90, "w", "search by Age"),
            ("email",   "Email",               260, "w", "search by Email"),
            ("courses", "Assigned Courses",    300, "w", "search by Course"),
        ],
        get_rows=lambda: [
            (i.instructor_id, i.name, i.age, i.email,
             ", ".join(f"{c.course_name} {c.course_id}" for c in i.assigned_courses))
            for i in INSTRUCTORS
        ],
    )
    instructors_tbl.frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))

    def instructor_selected():
        sel = instructors_tbl.tv.selection()
        if not sel: return None
        iid = instructors_tbl.tv.item(sel[0], "values")[0]
        for i in INSTRUCTORS:
            if i.instructor_id == iid:
                return i
        return None

    def on_edit_instructor():
        i = instructor_selected()
        if not i:
            messagebox.showinfo("Edit Instructor", "Select an instructor row first."); return
        edit_dialog_instructor(outer, i, on_ok=lambda: refresh_tables())

    def on_del_instructor():
        i = instructor_selected()
        if not i:
            messagebox.showinfo("Delete Instructor", "Select an instructor row first."); return
        if not messagebox.askyesno("Delete Instructor", f"Delete {i.name} ({i.instructor_id})?"):
            return
        unlink_instructor_from_everything(i)
        INSTRUCTORS.remove(i)
        refresh_tables()

    instructors_tbl.btn_edit.config(command=on_edit_instructor)
    instructors_tbl.btn_del.config(command=on_del_instructor)

    courses_tbl = FilterableTable(
        outer, "Courses",
        columns=[
            ("id",       "Course ID",         150, "w", "search by Course ID"),
            ("name",     "Course Name",       220, "w", "search by Name"),
            ("inst",     "Instructor",        200, "w", "search by Instructor"),
            ("students", "Enrolled Students", 340, "w", "search by Student"),
        ],
        get_rows=lambda: [
            (c.course_id, c.course_name,
             c.instructor.name if c.instructor else "",
             ", ".join(f"{s.student_id}-{s.name}" for s in c.enrolled_students))
            for c in COURSES
        ],
    )
    courses_tbl.frame.grid(row=2, column=0, sticky="nsew")

    def course_selected():
        sel = courses_tbl.tv.selection()
        if not sel: return None
        cid = courses_tbl.tv.item(sel[0], "values")[0]
        for c in COURSES:
            if c.course_id == cid:
                return c
        return None

    def on_edit_course():
        c = course_selected()
        if not c:
            messagebox.showinfo("Edit Course", "Select a course row first."); return
        edit_dialog_course(outer, c, on_ok=lambda: refresh_tables())

    def on_del_course():
        c = course_selected()
        if not c:
            messagebox.showinfo("Delete Course", "Select a course row first."); return
        if not messagebox.askyesno("Delete Course", f"Delete {c.course_name} ({c.course_id})?"):
            return
        unlink_course_from_everything(c)
        COURSES.remove(c)
        refresh_tables()

    courses_tbl.btn_edit.config(command=on_edit_course)
    courses_tbl.btn_del.config(command=on_del_course)

    def refresh_tables():
        students_tbl.refresh()
        instructors_tbl.refresh()
        courses_tbl.refresh()

    outer.refresh_tables = refresh_tables
    return outer





def build_save_load_bar(parent, on_refresh):
    bar = ttk.Frame(parent); bar.columnconfigure(5, weight=1)  

    def on_save():
        path = fd.asksaveasfilename(defaultextension=".json",
                                    filetypes=[("JSON","*.json")],
                                    title="Save data")
        if not path: return
        save_json(path, STUDENTS, INSTRUCTORS, COURSES)
        messagebox.showinfo("Save", "Data saved.")

    def on_load():
        path = fd.askopenfilename(filetypes=[("JSON","*.json")], title="Load data")
        if not path: return
        students, instructors, courses = load_json(path)
        STUDENTS[:] = students
        INSTRUCTORS[:] = instructors
        COURSES[:] = courses
        on_refresh()
        messagebox.showinfo("Load", "Data loaded.")

    def on_db_save():
        if DB_CONN is None:
            messagebox.showerror("Database", "No DB connection.")
            return
        try:
            save_all(DB_CONN, STUDENTS, INSTRUCTORS, COURSES)
            messagebox.showinfo("Database", "Saved to SQLite (school.db).")
        except Exception as e:
            messagebox.showerror("Database Save", str(e))

    def on_db_load():
        if DB_CONN is None:
            messagebox.showerror("Database", "No DB connection.")
            return
        try:
            students, instructors, courses = load_all(DB_CONN)
            STUDENTS[:] = students
            INSTRUCTORS[:] = instructors
            COURSES[:] = courses
            on_refresh()
            messagebox.showinfo("Database", "Loaded from SQLite (school.db).")
        except Exception as e:
            messagebox.showerror("Database Load", str(e))

    def on_db_backup():
        if DB_CONN is None:
            messagebox.showerror("Database", "No DB connection.")
            return
        path = fd.asksaveasfilename(
            title="Backup database to…",
            initialfile="school-backup.db",
            defaultextension=".db",
            filetypes=[("DB files","*.db"), ("All files","*.*")]
        )
        if not path:
            return
        try:
            backup_to(DB_CONN, path)
            messagebox.showinfo("Database", f"Backup written to:\n{path}")
        except Exception as e:
            messagebox.showerror("Database Backup", str(e))

    ttk.Button(bar, text="Save", command=on_save).grid(row=0, column=0, padx=4)
    ttk.Button(bar, text="Load", command=on_load).grid(row=0, column=1, padx=4)

    ttk.Separator(bar, orient="vertical").grid(row=0, column=2, padx=8, sticky="ns")
    ttk.Button(bar, text="DB Save",   command=on_db_save).grid(row=0, column=3, padx=4)
    ttk.Button(bar, text="DB Load",   command=on_db_load).grid(row=0, column=4, padx=4)
    ttk.Button(bar, text="DB Backup", command=on_db_backup).grid(row=0, column=5, padx=4)

    return bar

def build_forms_tab(parent, on_refresh):
    tab = ttk.Frame(parent, padding=0)

    scroller = ScrollableFrame(tab)
    scroller.pack(fill="both", expand=True, padx=8, pady=8)
    host = scroller.inner

    student_frame    = build_student_form(host, on_changed=on_refresh);    student_frame.pack(anchor="w", pady=4)
    instructor_frame = build_instructor_form(host, on_changed=on_refresh); instructor_frame.pack(anchor="w", pady=4)
    course_frame     = build_course_form(host, on_changed=on_refresh);     course_frame.pack(anchor="w", pady=4)

    reg_frame = build_registration_form(host, on_refresh=on_refresh); reg_frame.pack(anchor="w", pady=6)
    asg_frame = build_assignment_form(host, on_refresh=on_refresh);   asg_frame.pack(anchor="w", pady=6)

    tab.reg_frame = reg_frame
    tab.asg_frame = asg_frame
    return tab


def build_records_tab(parent, on_refresh):
    tab = ttk.Frame(parent, padding=0)

    scroller = ScrollableFrame(tab)
    scroller.pack(fill="both", expand=True, padx=8, pady=8)
    host = scroller.inner  

    tables = build_tables_and_search(host)
    tables.pack(fill="both", expand=True, pady=(0,8))

    bar = build_save_load_bar(host, on_refresh=on_refresh)
    bar.pack(fill="x", pady=6)

    tab.tables = tables
    return tab


def main():
    global DB_CONN

    root = tk.Tk()
    root.title("School Management System")
    root.geometry("980x820")

    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass

   
    try:
        DB_CONN = init_db("school.db")  
    except Exception as e:
        DB_CONN = None
        messagebox.showerror("Database", f"DB init failed: {e}")

    container = ttk.Frame(root, padding=10)
    container.pack(fill="both", expand=True)

    nb = ttk.Notebook(container)
    nb.pack(fill="both", expand=True)

    forms_tab = records_tab = None

    def global_refresh():
        records_tab.tables.refresh_tables()
        forms_tab.reg_frame.refresh_options()
        forms_tab.asg_frame.refresh_options()

    forms_tab   = build_forms_tab(nb, on_refresh=global_refresh)
    records_tab = build_records_tab(nb, on_refresh=global_refresh)

    nb.add(forms_tab,   text="Forms")
    nb.add(records_tab, text="Records & Search")

    global_refresh()
    nb.select(records_tab) 

    def _on_close():
        try:
            if DB_CONN is not None:
                DB_CONN.close()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()

if __name__ == "__main__":
    main()

