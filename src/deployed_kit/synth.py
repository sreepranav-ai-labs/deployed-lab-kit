"""Helpers for seeded synthetic data.

Every lab dataset is generated, never collected. Seeding makes it reproducible:
the same seed gives the same records, so answer keys and reports stay stable.
Identifier helpers deliberately produce values that cannot be real (for
example numbers in ranges no issuer uses), so planted personal data is safe.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

FIRST_NAMES = ["Anil", "Bhavani", "Chitra", "Deepak", "Esha", "Farhan", "Gowri", "Harish", "Indira", "Jagdish",
               "Kavya", "Lakshman", "Meena", "Naveen", "Padma", "Rahul", "Sarita", "Tarun", "Usha", "Venkat",
               "Yamuna", "Zoya", "Ravi", "Sunita", "Mohan", "Lata", "Prakash", "Rekha", "Suresh", "Anjali"]
LAST_NAMES = ["Rao", "Sharma", "Reddy", "Khan", "Naidu", "Patel", "Iyer", "Das", "Verma", "Singh",
              "Kumar", "Gupta", "Menon", "Joshi", "Pillai", "Yadav", "Bose", "Shetty", "Mishra", "Varma"]


class Synth:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)

    def pick(self, items):
        return self.rng.choice(items)

    def chance(self, p: float) -> bool:
        return self.rng.random() < p

    def name(self) -> str:
        return f"{self.pick(FIRST_NAMES)} {self.pick(LAST_NAMES)}"

    def day(self, start: date, end: date) -> date:
        return start + timedelta(days=self.rng.randint(0, (end - start).days))

    def fake_phone(self) -> str:
        """Ten digits starting with 5: not a valid Indian mobile number."""
        return "5" + "".join(str(self.rng.randint(0, 9)) for _ in range(9))

    def fake_national_id(self) -> str:
        """Twelve digits starting with 0, in groups of four: not a valid ID number."""
        digits = "0" + "".join(str(self.rng.randint(0, 9)) for _ in range(11))
        return f"{digits[:4]} {digits[4:8]} {digits[8:]}"
