import argparse
import sys
from cli.commands import cmd_version, cmd_status
from core.config import Config


def build_parser() -> argparse.ArgumentParser:
    """
    thsis function builds the argument parser for the CLI tool. It defines the available commands and their associated functions. The parser is configured to display help messages and handle command-line arguments.
    Returns:
        argparse.ArgumentParser: The configured argument parser.
    use the Config class to get the app_name from the configuration file. If not found, use a default value.
    case the user runs the CLI tool without any arguments, the parser will display the help message and exit gracefully.
    """
    config = Config()
    app_name = config.get("app_name", "Forex Tracker")

    parser = argparse.ArgumentParser(
        prog="forex", description=f"{app_name} CLI Analysis Tool"
    )
    subparsers = parser.add_subparsers(
        dest="command", title="Commands", description="Available Cli Action"
    )

    # Version command
    p_version = subparsers.add_parser(
        "version", help="Show current application version"
    )
    p_version.set_defaults(func=cmd_version)

    # Status command
    p_status = subparsers.add_parser(
        "status", help="Check system status and basic settings"
    )
    p_status.set_defaults(func=cmd_status)
    return parser


def main() -> None:
    """نقطة الدخول الرئيسية للأداة (Entry point).
    this function serves as the main entry point for the CLI tool. It builds the argument parser, processes command-line arguments, and executes the corresponding command functions based on user input.
    """
    parser = build_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
