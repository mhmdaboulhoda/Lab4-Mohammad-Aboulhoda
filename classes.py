from __future__ import annotations
import re
from typing import List, Optional

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _require_str(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} cannot be empty")
    return value.strip()

def _require_email(email: str) -> str:
    email = _require_str(email, "email")
    if not _EMAIL_RE.match(email):
        raise ValueError("email is not a valid address")
    return email

def _require_nonneg_int(n: int, field: str) -> int:
    if not isinstance(n, int):
        raise ValueError(f"{field} must be an integer")
    if n < 0:
        raise ValueError(f"{field} must be non-negative")
    return n

def _require_id(s: str, field: str) -> str:
    s = _require_str(s, field)
    if not re.match(r"^[A-Za-z0-9_\-]+$", s):
        raise ValueError(f"{field} may contain only letters, digits, '_' or '-'")
    return s

class Person:
    def __init__(self, name: str, age: int, email: str):
        self._name = _require_str(name, "name")
        self._age = _require_nonneg_int(age, "age")
        self.__email = _require_email(email) 

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = _require_str(value, "name")

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        self._age = _require_nonneg_int(value, "age")

    @property
    def email(self) -> str:
        return self.__email

    def set_email(self, new_email: str) -> None:
        self.__email = _require_email(new_email)

    def introduce(self) -> str:
        return f"Hi, my name is {self.name}, I am {self.age} years old."

    def to_base_dict(self) -> dict:
        return {"name": self.name, "age": self.age, "email": self.__email}

    @classmethod
    def from_base_dict(cls, d: dict) -> "Person":
        return cls(d["name"], int(d["age"]), d["email"])


class Student(Person):
    def __init__(self, name: str, age: int, email: str, student_id: str):
        super().__init__(name, age, email)
        self._student_id = _require_id(student_id, "student_id")
        self.registered_courses: List["Course"] = []

    @property
    def student_id(self) -> str:
        return self._student_id
    @student_id.setter
    def student_id(self, v: str) -> None:
        self._student_id = _require_str(str(v), "student_id")

    @property
    def name(self) -> str:
        return self._name
    @name.setter
    def name(self, v: str) -> None:
        self._name = _require_str(v, "name")

    @property
    def age(self) -> int:
        return self._age
    @age.setter
    def age(self, v) -> None:
        
        self._age = int(v)

    
    @property
    def email(self) -> str:
       
        return super().email

    @email.setter
    def email(self, v: str) -> None:
        
        self.set_email(v)



    def register(self, course: "Course") -> str:
        if not isinstance(course, Course):
            raise TypeError("register(course) requires a Course instance")
        if course in self.registered_courses:
            return f"{self.name} is already registered in {course.course_name}"
        self.registered_courses.append(course)
        if self not in course.enrolled_students:
            course.enrolled_students.append(self)
        return f"{self.name} registered for {course.course_name}"

    def to_dict(self) -> dict:
        base = self.to_base_dict()
        base.update({
            "student_id": self.student_id,
            "registered_course_ids": [c.course_id for c in self.registered_courses],
        })
        return base

    @classmethod
    def from_dict(cls, d: dict) -> "Student":
        s = cls(d["name"], int(d["age"]), d["email"], d["student_id"])
        s._pending_course_ids = list(d.get("registered_course_ids", []))
        return s


class Instructor(Person):
    def __init__(self, name: str, age: int, email: str, instructor_id: str):
        super().__init__(name, age, email)
        self._instructor_id = _require_id(instructor_id, "instructor_id")
        self.assigned_courses: List["Course"] = []

   

    @property
    def instructor_id(self) -> str:
        return self._instructor_id
    @instructor_id.setter
    def instructor_id(self, v: str) -> None:
        self._instructor_id = _require_str(str(v), "instructor_id")

    @property
    def name(self) -> str:
        return self._name
    @name.setter
    def name(self, v: str) -> None:
        self._name = _require_str(v, "name")

    @property
    def age(self) -> int:
        return self._age
    @age.setter
    def age(self, v) -> None:
        self._age = int(v)

    
    @property
    def email(self) -> str:
        return super().email

    @email.setter
    def email(self, v: str) -> None:
        self.set_email(v)


    
    

    def assign_course(self, course: "Course") -> str:
        if not isinstance(course, Course):
            raise TypeError("assign_course(course) requires a Course instance")
        if course not in self.assigned_courses:
            self.assigned_courses.append(course)
        if course.instructor is None:
            course.instructor = self
        elif course.instructor is not self:
            raise ValueError(
                f"{course.course_id} already has an instructor ({course.instructor.name}). "
                "Unassign first if reassignment is intended."
            )
        return f"{self.name} assigned to teach {course.course_name}"

    def to_dict(self) -> dict:
        base = self.to_base_dict()
        base.update({
            "instructor_id": self.instructor_id,
            "assigned_course_ids": [c.course_id for c in self.assigned_courses],
        })
        return base

    @classmethod
    def from_dict(cls, d: dict) -> "Instructor":
        i = cls(d["name"], int(d["age"]), d["email"], d["instructor_id"])
        i._pending_course_ids = list(d.get("assigned_course_ids", []))
        return i


class Course:
    def __init__(self, course_id: str, course_name: str, instructor: Optional[Instructor] = None):
        self._course_id = _require_id(course_id, "course_id")
        self._course_name = _require_str(course_name, "course_name")
        if instructor is not None and not isinstance(instructor, Instructor):
            raise TypeError("instructor must be an Instructor or None")
        self._instructor: Optional[Instructor] = instructor
        self.enrolled_students: List[Student] = []

    @property
    def course_id(self) -> str:
        return self._course_id

    @property
    def course_name(self) -> str:
        return self._course_name

    @course_name.setter
    def course_name(self, value: str) -> None:
        self._course_name = _require_str(value, "course_name")

    @property
    def instructor(self) -> Optional[Instructor]:
        return self._instructor

    @instructor.setter
    def instructor(self, value: Optional[Instructor]) -> None:
        if value is not None and not isinstance(value, Instructor):
            raise TypeError("instructor must be an Instructor or None")
        self._instructor = value
        if value is not None and self not in value.assigned_courses:
            value.assigned_courses.append(self)

    def add_student(self, student: Student) -> str:
        if not isinstance(student, Student):
            raise TypeError("add_student(student) requires a Student instance")
        if student in self.enrolled_students:
            return f"{student.name} is already enrolled in {self.course_name}"
        self.enrolled_students.append(student)
        if self not in student.registered_courses:
            student.registered_courses.append(self)
        return f"{student.name} enrolled in {self.course_name}"

    def to_dict(self) -> dict:
        return {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "instructor_id": self.instructor.instructor_id if self.instructor else None,
            "enrolled_student_ids": [s.student_id for s in self.enrolled_students],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Course":
        c = cls(d["course_id"], d["course_name"], None)
        c._pending_instructor_id = d.get("instructor_id")
        c._pending_student_ids = list(d.get("enrolled_student_ids", []))
        return c
