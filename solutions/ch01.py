"""
Solution: Identify Security Risks in Code Snippets

Uses pattern matching to detect common security risks in Python code.
"""

import re

# Patterns mapped to risk categories
RISK_PATTERNS = [
    # Filesystem risks
    (
        r"open\s*\([^)]*(/etc/|/proc/|/sys/|\.env|\.ssh|\.aws|\.pem|\.key|passwd|shadow)",
        "filesystem: access to sensitive path",
    ),
    (r"os\.walk\s*\(\s*['\"/]", "filesystem: directory traversal"),
    (r"os\.listdir\s*\(\s*['\"/]", "filesystem: directory listing"),
    (r"os\.remove|os\.unlink|shutil\.rmtree", "filesystem: file deletion"),
    # Network risks
    (
        r"urllib\.request\.urlopen|urllib\.request\.urlretrieve",
        "network: outbound HTTP request via urllib",
    ),
    (r"requests\.(get|post|put|delete|patch)\s*\(", "network: outbound HTTP request via requests"),
    (r"socket\.socket|\.connect\s*\(", "network: raw socket connection"),
    (r"http\.client\.|httplib", "network: outbound HTTP connection"),
    # Subprocess risks
    (
        r"subprocess\.(call|run|Popen|check_output|check_call)",
        "subprocess: command execution via subprocess",
    ),
    (r"os\.system\s*\(", "subprocess: command execution via os.system"),
    (r"os\.popen\s*\(", "subprocess: command execution via os.popen"),
    (r"os\.exec[a-z]*\s*\(", "subprocess: process replacement via os.exec"),
    # Resource exhaustion risks
    (r"os\.fork\s*\(", "resource: fork (potential fork bomb)"),
    (r"while\s+True.*\.(append|extend|insert)", "resource: unbounded memory allocation"),
]


def identify_risks(code: str) -> list[str]:
    """
    Analyze a code snippet and return a list of identified security risks.

    Args:
        code: A string containing Python source code to analyze.

    Returns:
        A list of strings, each describing a security risk found.
        Returns an empty list if no risks are detected.
    """
    risks = []
    # Flatten multiline code for pattern matching across lines
    flat = code.replace("\n", " __NL__ ")

    for pattern, description in RISK_PATTERNS:
        if re.search(pattern, flat, re.IGNORECASE):
            risks.append(description)

    return risks
