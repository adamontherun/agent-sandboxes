"""Tests for Chapter 8 challenge: package management and dependency resolution."""

from ch08 import DependencyPlan, parse_requirements, resolve_dependencies


class TestParseRequirements:
    def test_simple_packages(self):
        text = "requests\nflask\nnumpy"
        assert parse_requirements(text) == ["requests", "flask", "numpy"]

    def test_version_specifiers(self):
        text = "requests>=2.28\nflask==3.0.0\nnumpy~=1.24"
        assert parse_requirements(text) == ["requests", "flask", "numpy"]

    def test_comments_and_blanks(self):
        text = "# This is a comment\nrequests\n\n# Another comment\nflask\n"
        assert parse_requirements(text) == ["requests", "flask"]

    def test_inline_comments(self):
        text = "requests  # HTTP library\nflask  # web framework"
        assert parse_requirements(text) == ["requests", "flask"]

    def test_extras(self):
        text = "requests[security]\ncelery[redis,auth]"
        assert parse_requirements(text) == ["requests", "celery"]

    def test_environment_markers(self):
        text = "pywin32; sys_platform == 'win32'\nrequests"
        assert parse_requirements(text) == ["pywin32", "requests"]

    def test_dash_options_skipped(self):
        text = "-r other.txt\n--index-url https://pypi.org/simple\nrequests"
        assert parse_requirements(text) == ["requests"]

    def test_case_normalization(self):
        text = "Flask\nNumPy\nRequests"
        result = parse_requirements(text)
        assert result == ["flask", "numpy", "requests"]

    def test_empty_input(self):
        assert parse_requirements("") == []
        assert parse_requirements("# only comments") == []


class TestResolveDependencies:
    def test_all_available(self):
        plan = resolve_dependencies(["flask", "requests"], {"flask", "requests"})
        assert plan.already_available == ["flask", "requests"]
        assert plan.needs_install == []
        assert plan.install_command == ""

    def test_none_available(self):
        plan = resolve_dependencies(["pandas", "scipy"], {"flask"})
        assert plan.already_available == []
        assert plan.needs_install == ["pandas", "scipy"]
        assert plan.install_command == "pip install pandas scipy"

    def test_mixed(self):
        plan = resolve_dependencies(["flask", "pandas", "requests"], {"flask", "requests"})
        assert plan.already_available == ["flask", "requests"]
        assert plan.needs_install == ["pandas"]
        assert plan.install_command == "pip install pandas"

    def test_case_insensitive(self):
        plan = resolve_dependencies(["Flask", "NumPy"], {"flask", "numpy"})
        assert plan.already_available == ["Flask", "NumPy"]
        assert plan.needs_install == []

    def test_empty_requested(self):
        plan = resolve_dependencies([], {"flask"})
        assert plan.already_available == []
        assert plan.needs_install == []
        assert plan.install_command == ""

    def test_result_is_dataclass(self):
        plan = resolve_dependencies(["flask"], set())
        assert isinstance(plan, DependencyPlan)
