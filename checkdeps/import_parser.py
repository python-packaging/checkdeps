import ast
from pathlib import Path
from typing import Set


def get_imports(path: Path) -> Set[str]:
    tree = ast.parse(path.read_bytes())  # TODO can we get away with this
    imports: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for subnode in node.names:
                imports.add(subnode.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                for subnode in node.names:
                    imports.add(f"{node.module}.{subnode.name}")
    return imports
