import sys
import argparse
from src.live_detector import start_monitor


def main():
    parser = argparse.ArgumentParser(
        prog="aros-s",
        description="AROS-S on-board anomaly detector",
    )
    parser.add_argument(
        "--mitigation", choices=["on", "off"], default=None,
        help="enable/disable autonomous mitigation for this run "
             "(overrides AROS_MITIGATION; default: env value, or on)",
    )
    parser.add_argument(
        "--mode", choices=["UDP", "CSV"], default="UDP",
        help="telemetry source (default: UDP)",
    )
    args = parser.parse_args()

    # None -> let the env default decide; otherwise force on/off for this run
    mitigation = None if args.mitigation is None else (args.mitigation == "on")

    print("==================================================")
    print("AROS-S Autonomous Security")
    print("==================================================")

    try:
        start_monitor(mode=args.mode, mitigation=mitigation)
    except KeyboardInterrupt:
        print("\nAROS-S shutdown sequence initiated by Ground Control.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[CRITICAL] System failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
