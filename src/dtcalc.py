#!/opt/homebrew/bin/python3

import atexit
import os
import re
import readline
import sys
from datetime import datetime, timedelta

RESET = "\033[0m"
LIGHTBLUE = "\033[94m"
RED = "\033[91m"
GREEN = "\033[92m"

# -----------------------
# Persistent History Setup
# -----------------------
readline.set_history_length(1000)
HISTORY_FILE = os.path.expanduser("~/.dtcalc_history")
try:
  readline.read_history_file(HISTORY_FILE)
except FileNotFoundError:
  pass
atexit.register(readline.write_history_file, HISTORY_FILE)


# -----------------------
# Util methods
# -----------------------
def check_condition(condition, message):
  if not condition:
    raise ValueError(message)


# -----------------------
# Duration Parsing
# -----------------------
def parse_duration(s: str) -> timedelta:
  # Normalize unit names, with "weeks" mapped to "days"
  unit_map = {
    "w": "days",
    "week": "days",
    "weeks": "days",
    "d": "days",
    "day": "days",
    "days": "days",
    "h": "hours",
    "hr": "hours",
    "hour": "hours",
    "hours": "hours",
    "m": "minutes",
    "min": "minutes",
    "minute": "minutes",
    "minutes": "minutes",
    "s": "seconds",
    "sec": "seconds",
    "second": "seconds",
    "seconds": "seconds",
  }

  # Parse tokens like "2years", "3 days", "3w4d", etc.
  pattern = r"(\d+)\s*([a-zA-Z]+)"
  matches = re.findall(pattern, s, re.IGNORECASE)
  if not matches:
    return None

  kwargs = {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}

  for value, unit in matches:
    unit_key = unit_map.get(unit.lower())
    check_condition(unit_key, f"Unsupported duration unit: {unit}")
    val = int(value)
    # Expand weeks to days
    if unit_key == "days" and unit.lower().startswith("w"):
      val *= 7
    kwargs[unit_key] += val

  return timedelta(**kwargs)


# -----------------------
# Datetime Parsing
# -----------------------
def parse_datetime_safe(s: str) -> datetime:
  if s.lower() == "today":
    return datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
  elif s.lower() == "now":
    return datetime.now()

  date_formats = [
    "%Y-%m-%d",
    "%B/%d/%Y",
    "%B/%d/%y",
    "%b/%d/%Y",
    "%b/%d/%y",
    "%m/%d/%y",
    "%m/%d/%Y",
  ]
  time_formats = [
    "",
    "%H:%M",
    "%H:%M:%S",
    "%I:%M %p",
    "%I:%M:%S %p",
  ]
  for dfmt in date_formats:
    for tfmt in time_formats:
      fmt = f"{dfmt} {tfmt}".strip()
      try:
        return datetime.strptime(s, fmt)
      except ValueError:
        continue
  return None


# -----------------------
# Expression Evaluation
# -----------------------
def evaluate_expression(expr: str) -> datetime | timedelta:
  tokens = [s.strip() for s in re.split(r"\s+([+-])", expr) if s.strip()]

  result = None
  op = None

  for token in tokens:
    if token in ("+", "-"):
      # Consectuive operators are not allowed
      check_condition(op is None, f"Expecting an operand after operator '{op}'")
      op = token
      continue

    dur = parse_duration(token)
    if dur:
      if result is None:
        result = dur
      else:
        check_condition(op, "Missing operator")
        result = result + dur if op == "+" else result - dur
        op = None
      continue

    dt = parse_datetime_safe(token)
    check_condition(dt, f"Could not parse token: '{token}'")
    if result is None:
      result = dt
    else:
      check_condition(op, "Missing operator")
      if isinstance(result, datetime):
        check_condition(op == "-", "Cannot add two dates.")
        result = result - dt
      elif isinstance(result, timedelta):
        check_condition(op == "+", "Cannot subtract date from duration.")
        result = result + dt
      op = None
    continue

  check_condition(op is None, "Last token can not be an operator")
  check_condition(result, "No operands found")
  return result


# -----------------------
# Main Loop
# -----------------------
def print_help():
  print(
    "Usage:\n"
    "  dtcalc                      # Launch interactive mode\n"
    '  dtcalc "today + 3d"         # Command-line argument mode\n'
    '  echo "today + 3d" | dtcalc  # Piped input\n\n'
    "Expression format:\n"
    "  [datetime] [+|-] [duration]\n"
    "  [duration] [+|-] [duration]\n"
    "  [datetime] - [datetime]\n\n"
    "Examples:\n"
    "  today + 5d\n"
    "  2024-01-01 - 2023-01-01\n"
    "  now + 3h 15m"
  )


def get_prompt() -> None:
  return f"{LIGHTBLUE}> {RESET}"


def print_result(result) -> str:
  print(f"{LIGHTBLUE}= {RESET}{result}")


def print_error(result) -> str:
  print(f"{RED}! {RESET}{result}")


def format_datetime(dt: datetime) -> str:
  if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
    return dt.strftime("%Y-%m-%d")
  else:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_timedelta(td: timedelta) -> str:
  days = td.days
  total_seconds = int(td.total_seconds())
  hours, remainder = divmod(total_seconds % (24 * 3600), 3600)
  minutes, seconds = divmod(remainder, 60)

  parts = []
  if days:
    parts.append(f"{abs(days)} day{'s' if abs(days) != 1 else ''}")
  if hours:
    parts.append(f"{abs(hours)} hour{'s' if abs(hours) != 1 else ''}")
  if minutes:
    parts.append(f"{abs(minutes)} minute{'s' if abs(minutes) != 1 else ''}")
  if seconds:
    parts.append(f"{abs(seconds)} second{'s' if abs(seconds) != 1 else ''}")

  sign = "-" if total_seconds < 0 else ""
  return sign + ", ".join(parts) if parts else "0 seconds"


def process_expression(input: str) -> str:
  answer = evaluate_expression(input)
  # answer maybe one of timedelta (dur +/- dur, dt - dt) or datetime (dt +/- dur)
  if isinstance(answer, datetime):
    return format_datetime(answer)
  elif isinstance(answer, timedelta):
    return format_timedelta(answer)


def main():
  # Try to get expression from command line or stdin first
  expr = None
  if not sys.stdin.isatty():  # Piped input
    expr = sys.stdin.read().strip()
  elif len(sys.argv) > 1:  # Command-line arguments
    expr = " ".join(sys.argv[1:]).strip()
  # Execute expression if not None, then exit
  if expr:
    try:
      result = process_expression(expr)
      if result:
        print(result)
    except ValueError as e:
      print(f"Error: {e}", file=sys.stderr)
    return

  # Enter interactive mode if no expression is provided
  while True:
    try:
      user_input = input(get_prompt()).strip()
      if not user_input:
        continue
      elif user_input == "help":
        print_help()
        continue
      else:
        print_result(process_expression(user_input))
    except (EOFError, KeyboardInterrupt):
      print("\n👋 Bye!")
      break
    except ValueError as e:
      print_error(f"Error: {e}")


if __name__ == "__main__":
  main()
