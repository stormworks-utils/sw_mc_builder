from argparse import ArgumentParser


def parser_arguments(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--microcontroller",
        "-m",
        action="store_true",
        help="Export microcontrollers to Stormworks microcontroller directory",
    )
    parser.add_argument(
        "--vehicle",
        "-v",
        type=str,
        action="append",
        help="Export microcontrollers to vehicles. Can be used multiple times.",
    )
    parser.add_argument(
        "--select",
        "-s",
        type=str,
        action="append",
        help="Select, which microcontrollers to export based on their name. Can be used multiple times.",
    )
