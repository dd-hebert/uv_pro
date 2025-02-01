import importlib
import pkgutil


def discover_commands() -> dict:
    """Dynamically discover and import all CLI command modules."""
    package = "uv_pro.commands"
    modules = pkgutil.iter_modules(importlib.import_module(package).__path__)
    commands = {}

    for _, module_name, _ in modules:
        if not module_name.startswith("_"):
            module = importlib.import_module(f"{package}.{module_name}")
            commands[module_name] = module

    return commands


COMMANDS = discover_commands()
