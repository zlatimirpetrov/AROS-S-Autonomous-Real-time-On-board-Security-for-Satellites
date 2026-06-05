import sys
from src.live_detector import start_monitor

def main():
    print("==================================================")
    print("AROS-S Autonomous Security")
    print("==================================================")
    
    try:
        start_monitor(mode='UDP')
    except KeyboardInterrupt:
        print("\nAROS-S shutdown sequence initiated by Ground Control.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[CRITICAL] System failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()