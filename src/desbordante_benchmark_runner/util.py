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


def build_desbordante(
    desbordante_root: Path,
    *,
    benchmarks: bool = False,
    force_fetch_datasets: bool = False,
    target: str = "",
    disable_logging: bool = True,
) -> Path:
    (desbordante_root / "build" / "CMakeCache.txt").unlink(missing_ok=True)

    cmake_args = [
        "cmake",
        "-B",
        desbordante_root / "build",
        "-S",
        desbordante_root,
        "-G",
        "Ninja",
    ]
    if benchmarks:
        cmake_args += ["-D", "DESBORDANTE_BUILD_BENCHMARKS=ON"]
    input_data = desbordante_root / "build" / "target" / "input_data"
    fetch_datasets = (
        force_fetch_datasets
        or not input_data.exists()
        or len(list(input_data.iterdir())) == 0
    )
    if not fetch_datasets:
        cmake_args += ["-D", "DESBORDANTE_FETCH_DATASETS=OFF"]
    if disable_logging:
        cmake_args += ["-D", "DESBORDANTE_LOG_LEVEL=CRITICAL"]
    run(*cmake_args, cwd=desbordante_root)

    ninja_args = ["cmake", "--build", desbordante_root / "build"]
    if target:
        ninja_args += ["--target", target]
    run(*ninja_args, cwd=desbordante_root)

    build_target = desbordante_root / "build" / "target"
    assert build_target.exists()
    return build_target
