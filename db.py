import sqlite3
from pathlib import Path
from typing import Iterable, Tuple

from classes import Student, Instructor, Course

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS students(
  student_id TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  age        INTEGER NOT NULL,
  email      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS instructors(
  instructor_id TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  age           INTEGER NOT NULL,
  email         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses(
  course_id   TEXT PRIMARY KEY,
  course_name TEXT NOT NULL,
  instructor_id TEXT,
  FOREIGN KEY(instructor_id) REFERENCES instructors(instructor_id) ON DELETE SET NULL
);

-- many-to-many (student <-> course)
CREATE TABLE IF NOT EXISTS registrations(
  student_id TEXT NOT NULL,
  course_id  TEXT NOT NULL,
  PRIMARY KEY(student_id, course_id),
  FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
  FOREIGN KEY(course_id)  REFERENCES courses(course_id)  ON DELETE CASCADE
);
"""

def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn

def wipe(conn: sqlite3.Connection):
    conn.execute("DELETE FROM registrations")
    conn.execute("UPDATE courses SET instructor_id = NULL")
    conn.execute("DELETE FROM courses")
    conn.execute("DELETE FROM students")
    conn.execute("DELETE FROM instructors")
    conn.commit()

def save_all(conn: sqlite3.Connection,
             students: Iterable[Student],
             instructors: Iterable[Instructor],
             courses: Iterable[Course]):
    """Upserts everything from memory into the DB."""
    cur = conn.cursor()

    cur.executemany(
        "INSERT INTO students(student_id,name,age,email) VALUES(?,?,?,?) "
        "ON CONFLICT(student_id) DO UPDATE SET name=excluded.name, age=excluded.age, email=excluded.email",
        [(s.student_id, s.name, int(s.age), s.email) for s in students]
    )

    cur.executemany(
        "INSERT INTO instructors(instructor_id,name,age,email) VALUES(?,?,?,?) "
        "ON CONFLICT(instructor_id) DO UPDATE SET name=excluded.name, age=excluded.age, email=excluded.email",
        [(i.instructor_id, i.name, int(i.age), i.email) for i in instructors]
    )

    cur.executemany(
        "INSERT INTO courses(course_id,course_name) VALUES(?,?) "
        "ON CONFLICT(course_id) DO UPDATE SET course_name=excluded.course_name",
        [(c.course_id, c.course_name) for c in courses]
    )

    for c in courses:
        cur.execute("UPDATE courses SET instructor_id=? WHERE course_id=?",
                    (c.instructor.instructor_id if c.instructor else None, c.course_id))

    cur.execute("DELETE FROM registrations")
    cur.executemany(
        "INSERT INTO registrations(student_id,course_id) VALUES(?,?)",
        [(s.student_id, c.course_id) for s in students for c in getattr(s, "registered_courses", [])]
    )

    conn.commit()

def load_all(conn: sqlite3.Connection) -> Tuple[list, list, list]:
    """Reads all rows and rebuilds in-memory object graph."""
    from classes import Student, Instructor, Course  

    cur = conn.cursor()
    
    cur.execute("SELECT student_id,name,age,email FROM students ORDER BY student_id")
    rows = cur.fetchall()
    students = [Student(name=r[1], age=int(r[2]), email=r[3], student_id=r[0]) for r in rows]
    S = {s.student_id: s for s in students}

    cur.execute("SELECT instructor_id,name,age,email FROM instructors ORDER BY instructor_id")
    rows = cur.fetchall()
    instructors = [Instructor(name=r[1], age=int(r[2]), email=r[3], instructor_id=r[0]) for r in rows]
    I = {i.instructor_id: i for i in instructors}

    cur.execute("SELECT course_id,course_name,instructor_id FROM courses ORDER BY course_id")
    rows = cur.fetchall()
    courses = []
    C = {}
    for cid, cname, iid in rows:
        ins = I.get(iid) if iid else None
        c = Course(course_id=cid, course_name=cname, instructor=ins)
        courses.append(c)
        C[cid] = c

    cur.execute("SELECT student_id, course_id FROM registrations")
    for sid, cid in cur.fetchall():
        s = S.get(sid)
        c = C.get(cid)
        if s and c:
            s.register(c) 

    return students, instructors, courses

def backup_to(conn: sqlite3.Connection, backup_path: str):
    Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(backup_path) as dest:
        conn.backup(dest)
