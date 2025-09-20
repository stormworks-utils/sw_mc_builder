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
        help="Export microcontrollers to vehicles. Separated by commas.",
    )
    parser.add_argument(
        "--select",
        "-s",
        type=str,
        help="Select, which microcontrollers to export based on their name. Separated by commas.",
    )
