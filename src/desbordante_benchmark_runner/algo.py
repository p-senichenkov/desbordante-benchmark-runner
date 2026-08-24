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
