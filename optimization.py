from __future__ import annotations

from typing import List, Tuple
import math
from dataclasses import dataclass
import random
import time


tolerance = 1e-12


@dataclass
class Constraint:
    data: Tuple[float, float, float]

    def __getitem__(self, idx: int) -> float:
        return self.data[idx]

    def is_valid(self) -> bool:
        return self.data[1] <= self.data[2]

    def dx_bottom_branch(self, s: float) -> float:
        return -self.data[0] * s + self.data[1]

    def dx_top_branch(self, s: float) -> float:
        return -self.data[0] * s + self.data[2]

    def verify(self, s: float, dx: float) -> bool:
        return self.data[2] + tolerance >= self.data[0] * s + dx >= self.data[1] - tolerance

    def dx_interval(self, s: float) -> Tuple[float, float]:
        return -self.data[0] * s + self.data[1], -self.data[0] * s + self.data[2]

    @classmethod
    def make(cls, x: float, y: float, z: float) -> Constraint:
        return Constraint((x, y, z))

    @classmethod
    def make_random(cls) -> Constraint:
        return Constraint((random.uniform(-10, 10), random.uniform(-100, 0), 1000 + random.uniform(-100, 0)))


def generate_constraints_empty() -> List[Constraint]:
    return []


def generate_constraints_single() -> List[Constraint]:
    return [Constraint.make(1, 2, 3)]


def generate_constraints_table() -> List[Constraint]:
    return [Constraint.make(-1.0, -5, 2),
            Constraint.make(-1.0 / 3.0, -2, 5),
            Constraint.make(-1.0 / 2.0, -4, 3),
            Constraint.make(-3.0 / 2.0, -7, 1)]


def generate_constraints_random(n_constraints: int) -> List[Constraint]:
    result: List[Constraint] = list()
    for _ in range(n_constraints):
        result.append(Constraint.make_random())
    return result


def all_valid_constraints(cons: List[Constraint]) -> bool:
    for c in cons:
        if not c.is_valid():
            return False
    return True


def has_solutions(cons: List[Constraint]) -> bool:
    return max(cons, key=lambda c: c[1])[1] <= min(cons, key=lambda c: c[2])[2]


def has_infinite_solutions(cons: List[Constraint]) -> bool:
    all_the_same: bool = True
    for idx in range(1, len(cons)):
        if cons[idx][0] != cons[0][0]:
            all_the_same = False
            break
    return all_the_same


def verify(cons: List[Constraint], s: float, dx: float) -> bool:
    for c in cons:
        if not c.verify(s, dx):
            return False
    return True


def dx_interval(cons: List[Constraint], s: float) -> Tuple[float, float]:
    interval: Tuple[float, float] = (-math.inf, math.inf)
    for c in cons:
        current_interval: Tuple[float, float] = c.dx_interval(s)
        interval = max(interval[0], current_interval[0]), min(interval[1], current_interval[1])
    return interval


def dx_interval_mid(cons: List[Constraint], s: float) -> float:
    interval = dx_interval(cons, s)
    return 0.5 * (interval[0] + interval[1])


def solve(cons: List[Constraint]) -> Tuple[float, float]:
    if not cons or not has_solutions(cons):
        return 0.0, 0.0
    if has_infinite_solutions(cons):
        return math.inf, 0.0

    constraint_idx, _ = max(enumerate(cons), key=lambda ic: ic[1][1])

    continue_flag: bool = True
    s_current_max: float = math.inf
    dx: float = 0.0
    while continue_flag:
        constraint_idx_candidate: int = constraint_idx
        s_current_max = math.inf
        for idx in range(len(cons)):
            if idx == constraint_idx:
                continue
            if cons[idx][0] == cons[constraint_idx][0]:
                continue
            if cons[idx][0] < cons[constraint_idx][0]:
                s_candidate: float = (cons[constraint_idx][1] - cons[idx][1]) / (cons[constraint_idx][0] - cons[idx][0])
                if s_candidate < s_current_max:
                    s_current_max = s_candidate
                    continue_flag = True
                    constraint_idx_candidate = idx
            else:
                s_candidate = (cons[idx][2] - cons[constraint_idx][1]) / (cons[idx][0] - cons[constraint_idx][0])
                if s_candidate < s_current_max:
                    s_current_max = s_candidate
                    continue_flag = False
                    constraint_idx_candidate = idx
        constraint_idx = constraint_idx_candidate
        dx = cons[constraint_idx].dx_top_branch(s_current_max)
    return s_current_max, dx


def solve_and_test(cons: List[Constraint]) -> None:
    if not cons:
        print('no constraints')
        return
    if not all_valid_constraints(cons):
        print('has invalid constraints')
        return
    if not has_solutions(cons):
        print('no solutions')
        return
    if has_infinite_solutions(cons):
        print('infinite solutions')
        return
    s, dx = solve(cons)
    interval = dx_interval(cons, s)
    if verify(cons, s, dx):
        if abs(interval[1] - interval[0]) < tolerance:
            return
        else:
            print('ERROR! Large interval')
    else:
        print('ERROR! Constraint violation!')


if __name__ == '__main__':
    # solve_and_test(generate_constraints_empty())
    # solve_and_test(generate_constraints_single())
    solve_and_test(generate_constraints_table())

    random.seed(time.time())
    start = time.time()
    for _ in range(10000):
        solve_and_test(generate_constraints_random(1000))
    end = time.time()
    print('time elapsed', end - start, 's')
