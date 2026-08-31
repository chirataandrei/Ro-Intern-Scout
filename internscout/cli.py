from __future__ import annotations

import argparse
import importlib.util

from internscout.config import ROOT


def _load_probe():
    path = ROOT / "tools" / "probe_ats.py"
    spec = importlib.util.spec_from_file_location("probe_ats", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan SWE/data/quant internships in Romania, remote-EU internships, and spring weeks."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="scan",
        choices=["scan", "apify-refresh", "discover", "probe"],
    )
    parser.add_argument("--email", action="store_true", help="Send the digest by email (SMTP_* / EMAIL_TO)")
    parser.add_argument("--no-save", action="store_true", help="Do not update data/seen.json")
    parser.add_argument("--dry-run", action="store_true", help="Print Apify actor input and estimated cost, no network")
    parser.add_argument("--write", action="store_true", help="probe: merge live boards into catalog shards")
    parser.add_argument("--limit", type=int, default=0, help="probe: only the first N candidates")
    parser.add_argument("--from-discovered", action="store_true", help="probe: use data/discovered.json")
    args = parser.parse_args(argv)

    if args.command == "scan":
        from internscout.runner import run

        return run(send=args.email, persist=not args.no_save)

    if args.command == "apify-refresh":
        from internscout.discover import apify_refresh

        return apify_refresh(dry_run=args.dry_run)

    if args.command == "discover":
        from internscout.discover import run_discovery

        run_discovery(dry_run=args.dry_run)
        return 0

    if args.command == "probe":
        probe = _load_probe()
        probe_argv: list[str] = []
        if args.write:
            probe_argv.append("--write")
        if args.from_discovered:
            probe_argv.append("--from-discovered")
        if args.limit:
            probe_argv.extend(["--limit", str(args.limit)])
        return int(probe.main(probe_argv))

    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
