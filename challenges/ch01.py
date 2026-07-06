"""
Challenge: Identify Security Risks in Code Snippets

Implement a function that scans a Python code snippet (as a string) and
returns a list of human-readable descriptions of security risks it finds:
filesystem access to sensitive paths, outbound network calls, subprocess/
command execution, and resource-exhaustion patterns like fork bombs.

This is the kind of static check an agent sandbox's control plane might run
BEFORE handing code to a MicroVM for execution — cheap, imperfect, defense
in depth alongside the VM-level isolation, not a replacement for it.
"""


def identify_risks(code: str) -> list[str]:
    """
    Analyze a code snippet and return a list of identified security risks.

    Args:
        code: A string containing Python source code to analyze.

    Returns:
        A list of strings, each describing a security risk found.
        Returns an empty list if no risks are detected.
    """
    raise NotImplementedError
