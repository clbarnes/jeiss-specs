"""
Read LabView's internal docs for file memory layout,
and extract useful information from it as a TSV.
"""
import re
from pathlib import Path
from argparse import ArgumentParser
from itertools import zip_longest
from dataclasses import dataclass


@dataclass
class Row:
    offset: int
    dtype: str
    description: str
    max_elements: int = 0

    def to_str(self, sep="\t"):
        return sep.join(
            [
                str(self.offset),
                self.dtype,
                str(self.max_elements),
                self.description.strip(),
            ]
        )

    def headers(self):
        return ["offset", "dtype", "max_elements", "description"]

    def dtype_nbytes(self):
        n = self.dtype[2:]
        if n == "?":
            return None
        return int(n)


def read_labview_doc(fpath: Path):
    regex = re.compile(
        r"^(?P<offset>\d+)\s+(?P<dtype>\w[\w\d]+)\s+(?P<description>\S.*)$"
    )

    dtype_map = {
        "BLN": ">u1",
        "SGL": ">f4",
        "DBL": ">f8",
        "STR": ">S?",
    }
    for sign in "ui":
        for pow in range(0, 4):
            nbytes = 2**pow
            dtype_map[f"{sign.upper()}{nbytes*8}"] = f">{sign}{nbytes}"

    rows = []
    with open(fpath) as f:
        for line in f:
            m = regex.match(line.rstrip())
            if not m:
                continue
            d = m.groupdict()
            rows.append(Row(int(d["offset"]), dtype_map[d["dtype"]], d["description"]))

    rows.sort(key=lambda r: r.offset)

    return rows


def infer_string_length(rows: list[Row]):
    next_it = iter(rows)
    next(next_it)
    for current_row, next_row in zip_longest(rows, next_it):
        if not current_row.dtype == ">S?":
            continue

        if next_row is None:
            if current_row.offset < 1024:
                next_offset = 1024
            else:
                raise RuntimeError("Unknown next offset")
        else:
            next_offset = next_row.offset

        length = next_offset - current_row.offset
        current_row.dtype = f">S{length}"

    return rows


def infer_max_elements(rows: list[Row]):
    next_it = iter(rows)
    next(next_it)
    for current_row, next_row in zip_longest(rows, next_it):
        nbytes = current_row.dtype_nbytes()
        if nbytes is None:
            continue

        if next_row is None:
            next_offset = 1024
        else:
            next_offset = next_row.offset

        length = next_offset - current_row.offset

        current_row.max_elements = length // nbytes

    return rows


def write_tsv_buffer(rows, buf=None):
    print("\t".join(rows[0].headers()), file=buf)
    for row in rows:
        print(row.to_str(), file=buf)


def write_tsv(rows, fpath):
    if str(fpath) == "-":
        fpath = None

    if fpath is None:
        write_tsv_buffer(rows)
    else:
        with open(fpath, "w") as f:
            write_tsv_buffer(rows, f)


def main(args=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "inpath",
        type=Path,
        help="Path to text file containing LabView internal documentation on metadata",
    )
    parser.add_argument(
        "outpath", nargs="?", help="Path to write TSV to (stdout if not given)"
    )
    parser.add_argument(
        "--infer-string-length",
        "-s",
        action="store_true",
        help="Infer the length of strings based on the next filled offset.",
    )

    parsed = parser.parse_args(args)

    rows = read_labview_doc(parsed.inpath)

    if parsed.infer_string_length:
        infer_string_length(rows)

    infer_max_elements(rows)

    write_tsv(rows, parsed.outpath)


if __name__ == "__main__":
    main()
