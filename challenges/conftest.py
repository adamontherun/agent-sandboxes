import importlib.util
import os
import sys
from pathlib import Path

if os.environ.get("COURSE_SOLUTIONS"):
    solutions_dir = Path(__file__).parent.parent / "solutions"
    for path in solutions_dir.glob("ch*.py"):
        name = path.stem
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[name] = module
