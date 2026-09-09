"""The flag file this application ships with.

Percentages are edited here when a rollout moves; ``allow=`` holds the staff
accounts that get a feature early and ``deny=`` the accounts that opted out.
"""

from flags.registry import Registry

FLAG_FILE = """
beta_search: off 100%      # paused after the latency regression
csv_export: 0% allow=user-7
dark_mode: 50%
holiday_theme: 0%          # staged for the launch, not started yet
new_editor: 100% deny=user-13
"""

REGISTRY = Registry.from_text(FLAG_FILE)
