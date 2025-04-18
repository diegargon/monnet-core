"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent

Global Vars

"""

AGENT_VERSION = "0.172"
# Config file
CONFIG_AGENT_PATH = "/etc/monnet/agent-config"
DATASTORE_FILE_PATH = "/tmp/datastore.json"
# Track timers
timers = {}

# Threshold
ALERT_THRESHOLD = 90
WARN_THRESHOLD = 80

# Timer Stats interval
TIMER_STATS_INTERVAL = 300

# Events
EVENT_EXPIRATION = 86400
