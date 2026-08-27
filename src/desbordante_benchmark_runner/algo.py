import typing as tp
from enum import StrEnum


class EPacAlgo(StrEnum):
    DOMAIN_PAC = "domain-pac"
    FD_PAC = "fd-pac"
    UCC_PAC = "ucc-pac"


# Human-readable names
ALGO_NAMES: dict[EPacAlgo, str] = {
    EPacAlgo.DOMAIN_PAC: "Domain PAC verifier",
    EPacAlgo.FD_PAC: "FD PAC verifier",
    EPacAlgo.UCC_PAC: "UCC PAC verifier",
}


ALGO_CLASSES: dict[EPacAlgo, str] = {
    EPacAlgo.DOMAIN_PAC: "DomainPACVerifier",
    EPacAlgo.FD_PAC: "FDPACVerifier",
    EPacAlgo.UCC_PAC: "UCCPACVerifier",
}


def sorted_algos(algos: tp.Iterable[EPacAlgo]) -> list[EPacAlgo]:
    result: list[EPacAlgo] = []
    for algo in EPacAlgo:
        if algo in algos:
            result.append(algo)
    return result
