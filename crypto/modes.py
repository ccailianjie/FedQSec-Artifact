"""Public mode and action definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CryptoMode(str, Enum):
    SIGNATURE = "signature"
    ENCRYPTION = "encryption"
    SIGNCRYPTION = "signcryption"

    @property
    def uses_authentication(self) -> bool:
        return self in {CryptoMode.SIGNATURE, CryptoMode.SIGNCRYPTION}

    @property
    def uses_confidentiality(self) -> bool:
        return self in {CryptoMode.ENCRYPTION, CryptoMode.SIGNCRYPTION}


@dataclass(frozen=True)
class SecurityAction:
    parameter_profile: str
    mode: CryptoMode

