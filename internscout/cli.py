from __future__ import annotations

import argparse

from internscout.scan import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan SWE/data/quant internships in Romania and quant student programmes."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="scan",
        choices=["scan"],
        help="Command (currently only scan)",
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="Send the digest by email (SMTP_* / EMAIL_TO)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not update data/seen.json",
    )
    args = parser.parse_args(argv)
    return run(send=args.email, persist=not args.no_save)


if __name__ == "__main__":
    raise SystemExit(main())
