import os
import subprocess
import typing as tp
from pathlib import Path

IOWAS_SIZES = [sz * 1000 for sz in [5, 10, 20, 50, 100, 200, 450, 550, 650]]


def toksyntax(num: int) -> str:
    magnitude_k = 0
    while num % 1000 == 0:
        magnitude_k += 1
        num //= 1000
    return f"{num}{'k' * magnitude_k}"


def iowa_fname(rows: int) -> Path:
    return Path(f"iowa{toksyntax(rows)}.csv")


def timed_run(test_name: str) -> int:
    """
    Returns:
        milliseconds
    """
    proc = subprocess.run(
        "Desbordante.benchmark", check=True, stdout=subprocess.PIPE, text=True
    )
    lines = proc.stdout.splitlines()
    assert len(lines) == 1
    return int(lines[0])


# Fix absolutely harmful default check=False
def run(*args: str | os.PathLike, **kwargs: tp.Any) -> None:
    subprocess.run(args, check=True, **kwargs)


def capture(*args: str | os.PathLike, **kwargs: tp.Any) -> str:
    proc = subprocess.run(args, check=True, stdout=subprocess.PIPE, text=True, **kwargs)
    return proc.stdout


def check_desbordante_root(desbordante_root: Path) -> None:
    assert desbordante_root.is_dir()
    assert (desbordante_root / ".git").is_dir(), (
        f"{desbordante_root} is not a git repository"
    )


def prepare_iowas(desbordante_root: Path) -> None:
    input_data = desbordante_root / "build" / "target" / "input_data"

    for iowa_size in IOWAS_SIZES:
        out_file = input_data / iowa_fname(iowa_size)
        if not out_file.exists() or out_file.stat().st_size == 0:
            with open(out_file, "wb") as iowa_out:
                run(
                    "head",
                    "-n",
                    str(iowa_size + 1),
                    input_data / iowa_fname(1_000_000),
                    stdout=iowa_out,
                )
