#!/usr/bin/env python3
"""Ensure that specs do not contain overlapping values.
"""
from argparse import ArgumentParser
from collections import defaultdict
import csv
import sys
from typing import NamedTuple, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Row(NamedTuple):
    name: str
    dtype: str
    offset: int
    shape: tuple[Union[int, str], ...]

    def item_size(self):
        chars = list(self.dtype)
        out = []
        while chars:
            last = chars.pop()
            if last.isnumeric():
                out.append(last)
            else:
                break
        return int("".join(reversed(out)))

    def n_items(self):
        out = 1
        for s in self.shape:
            if isinstance(s, str):
                logger.info(
                    "Variable shape at offset %s; assuming minimum (1)", self.offset
                )
                s = 1

            out *= max(1, s)
        return out

    def n_bytes(self):
        return self.item_size() * self.n_items()

    def interval(self):
        return (self.offset, self.offset + self.n_bytes())

    def variables(self):
        return {s for s in self.shape if isinstance(s, str)}


def parse_shape(s: str) -> tuple[Union[str, int], ...]:
    return tuple(int(val) if val.isnumeric() else val for val in s.split(","))


def read_tsv(fpath: Path) -> list[Row]:
    out = []
    with open(fpath) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for d in reader:
            row = Row(
                d["name"],
                d["dtype"],
                int(d["offset"]),
                parse_shape(d["shape"]),
            )
            out.append(row)
    return out


def find_problems(rows: list[Row]) -> bool:
    byte_map = defaultdict(list)
    names = set()

    has_problems = False

    for row in rows:
        if row.name in names:
            logger.critical("Found duplicate name: %s", row.name)
            has_problems = True
        else:
            names.add(row.name)

        for var in row.variables():
            if var not in names:
                logger.critical("Variable used before definition: %s", var)
                has_problems = True

        for idx in range(*row.interval()):
            byte_map[idx].append(row.name)

    for idx in range(1024, max(byte_map) + 1):
        byte_map[idx].append("ImageData")

    overlaps = defaultdict(set)

    for idx, names in byte_map.items():
        if len(names) < 2:
            continue
        overlaps[tuple(sorted(names))].add(idx)
        has_problems = True

    for k, v in overlaps.items():
        logger.critical(
            "Byte range [%s, %s] is assigned to all of %s", min(v), max(v), k
        )

    return has_problems


def process_file(fpath: Path):
    logger.info("Processing %s", fpath)
    rows = read_tsv(fpath)
    return find_problems(rows)


def main(args=None):
    logging.basicConfig(level=logging.INFO)

    parser = ArgumentParser()
    parser.add_argument(
        "path",
        nargs="*",
        type=Path,
        help="Path to a TSV file(s)",
    )

    parsed = parser.parse_args(args)
    has_problems = False

    for fpath in parsed.path:
        has_problems = process_file(fpath) or has_problems

    sys.exit(int(has_problems))


if __name__ == "__main__":
    main()
