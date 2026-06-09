"""Testes do Sandbox: classificação de tiers e bloqueio de padrões."""

import pytest

from valen.domains.tools.sandbox import (
    ExecutionTier,
    SandboxViolation,
    assert_not_blocked,
    classify_command,
    is_blocked,
    requires_approval,
)


@pytest.mark.parametrize(
    ("command", "tier"),
    [
        ("ls -la", ExecutionTier.READ_ONLY),
        ("cat /etc/hostname", ExecutionTier.READ_ONLY),
        ("mkdir build", ExecutionTier.REVERSIBLE),
        ("cp a b", ExecutionTier.REVERSIBLE),
        ("curl -X POST http://x", ExecutionTier.REVERSIBLE),
        ("rm file.txt", ExecutionTier.DESTRUCTIVE),
        ("mv a b", ExecutionTier.DESTRUCTIVE),
        ("sed -i s/a/b/ f", ExecutionTier.DESTRUCTIVE),
        ("docker ps", ExecutionTier.SYSTEM_LEVEL),
        ("systemctl restart x", ExecutionTier.SYSTEM_LEVEL),
        ("unknownbinary --x", ExecutionTier.SYSTEM_LEVEL),  # fail-safe: eleva
    ],
)
def test_classify_command(command, tier):
    assert classify_command(command) == tier


@pytest.mark.parametrize(
    "command",
    ["rm -rf /", "rm -rf  *", "dd if=/dev/zero", "sudo rm x", "reboot",
     "chmod 777 /etc", "killall python", "mkfs.ext4 /dev/sda"],
)
def test_blocked_patterns(command):
    assert is_blocked(command) is True
    with pytest.raises(SandboxViolation):
        assert_not_blocked(command)


def test_safe_command_not_blocked():
    assert is_blocked("ls -la") is False
    assert_not_blocked("ls -la")  # não levanta


def test_requires_approval():
    assert requires_approval(ExecutionTier.DESTRUCTIVE)
    assert requires_approval(ExecutionTier.SYSTEM_LEVEL)
    assert not requires_approval(ExecutionTier.READ_ONLY)
    assert not requires_approval(ExecutionTier.REVERSIBLE)
