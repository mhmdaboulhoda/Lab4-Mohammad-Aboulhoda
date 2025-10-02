import json
from classes import Student, Instructor, Course

def save_json(filepath, students, instructors, courses):
    data = {
        "students": [s.to_dict() for s in students],
        "instructors": [i.to_dict() for i in instructors],
        "courses": [c.to_dict() for c in courses],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    students = [Student.from_dict(d) for d in raw.get("students", [])]
    instructors = [Instructor.from_dict(d) for d in raw.get("instructors", [])]
    courses = [Course.from_dict(d) for d in raw.get("courses", [])]

    S = {s.student_id: s for s in students}
    I = {i.instructor_id: i for i in instructors}
    C = {c.course_id: c for c in courses}

    for c in courses:
        if c._pending_instructor_id:
            c.instructor = I.get(c._pending_instructor_id)
            if c.instructor and c not in c.instructor.assigned_courses:
                c.instructor.assigned_courses.append(c)
        for sid in c._pending_student_ids:
            s = S.get(sid)
            if s:
                c.enrolled_students.append(s)
                if c not in s.registered_courses:
                    s.registered_courses.append(c)

    for s in students:
        for cid in getattr(s, "_pending_course_ids", []):
            c = C.get(cid)
            if c and c not in s.registered_courses:
                s.registered_courses.append(c)
            if c and s not in c.enrolled_students:
                c.enrolled_students.append(s)

    for i in instructors:
        for cid in getattr(i, "_pending_course_ids", []):
            c = C.get(cid)
            if c and c not in i.assigned_courses:
                i.assigned_courses.append(c)
            if c and (c.instructor is None):
                c.instructor = i

    return students, instructors, courses
