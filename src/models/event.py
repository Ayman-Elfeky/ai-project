from dataclasses import dataclass
from typing import Optional


@dataclass
class Lecturer:
	id: str
	name: str


@dataclass
class Course:
	id: str
	name: str
	hours_per_week: int
	lecturer_id: Optional[str] = None


@dataclass
class Room:
	id: str
	name: str
	capacity: Optional[int] = None

