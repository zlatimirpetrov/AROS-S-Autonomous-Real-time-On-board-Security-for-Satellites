import os
import socket
from src.secure_cmd import sign

#proportionate response per detecting layer
_RESPONSE = {
    "Forest":     "ISOLATE_POWER",   #shed/isolate the anomalous power load
    "Neural Net": "KILL_PROCESS",    #terminate the offending process
    "Temporal":   "SAFE_MODE",       #slow drift -> safe-mode
}


def _truthy(v):
    return str(v).strip().lower() in ("1", "true", "on", "yes")


class Responder:
    def __init__(self, streak=3, grace=8, enabled=None):
        #explicit arg (from a CLI flag) wins; otherwise fall back to the env default
        if enabled is None:
            enabled = _truthy(os.getenv("AROS_MITIGATION", "on"))
        self.enabled = enabled
        self.host = os.getenv("AROS_CMD_HOST", "127.0.0.1")
        self.port = int(os.getenv("AROS_CMD_PORT", 5006))
        self.streak_needed = streak
        self.grace = grace
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # state machine
        self.streak = 0
        self.awaiting = False
        self.grace_left = 0
        if self.enabled:
            print(f"[Responder] mitigation ENABLED (streak={streak}, grace={grace})")
        else:
            print("[Responder] mitigation DISABLED (detect-and-log only)")

    def _send(self, action, cause, source):
        try:
            self.sock.sendto(sign(action, reason=cause, source=source),
                             (self.host, self.port))
        except Exception as e:
            print(f"  (command channel error: {e})")

    def handle(self, status, source, cause):
        """Advance the response state machine for one packet.
        Returns a mitigation label for logging ('-' if nothing fired)."""
        if not self.enabled:
            return "-"

        #watch for recovery / escalate
        if self.awaiting:
            if status == "Nominal":
                print("  >> RECOVERY confirmed: telemetry back to nominal.")
                self.awaiting = False
                self.streak = 0
            else:
                self.grace_left -= 1
                if self.grace_left <= 0:
                    self._send("SAFE_MODE", cause, source)
                    print("  >> ESCALATION: response did not restore nominal; commanded SAFE-MODE.")
                    self.awaiting = False
                    self.streak = 0
                    return "SAFE_MODE"
            return "-"

        #count consecutive anomalies, act once the streak is reached
        self.streak = self.streak + 1 if status != "Nominal" else 0
        if self.streak == self.streak_needed:
            action = _RESPONSE.get(source, "SAFE_MODE")
            self._send(action, cause, source)
            print(f"  >> MITIGATION: sustained {cause} anomaly ({source}); issued {action}.")
            self.awaiting = True
            self.grace_left = self.grace
            return action
        return "-"
