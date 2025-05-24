import re
import os
import readline
import atexit
from datetime import datetime, timedelta
from colorama import Fore, Style, init

init(autoreset=True)

# -----------------------
# Persistent History Setup
# -----------------------
HISTORY_FILE = os.path.expanduser("~/.dtcalc_history")
try:
  readline.read_history_file(HISTORY_FILE)
except FileNotFoundError:
  pass
atexit.register(readline.write_history_file, HISTORY_FILE)


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

  # Parse tokens like "2years", "3days", etc.
  pattern = r"(\d+)([a-zA-Z]+)"
  matches = re.findall(pattern, s, re.IGNORECASE)
  if not matches:
    return None

  kwargs = {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}

  for value, unit in matches:
    unit_key = unit_map.get(unit.lower())
    if not unit_key:
      raise ValueError(f"Unsupported duration unit: {unit}")
    val = int(value)
    if unit_key == "days" and unit.lower().startswith("w"):
      # Expand weekds to days
      val *= 7
    kwargs[unit_key] += val

  return timedelta(**kwargs)


# -----------------------
# Datetime Parsing
# -----------------------
def parse_datetime_safe(s: str) -> datetime:
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
  raise ValueError(f"Invalid date: {s}")


# -----------------------
# Expression Evaluation
# -----------------------
def evaluate_expression(expr: str):
  tokens = re.split(r"\s+([+-])\s+", expr.strip())
  if not tokens or len(tokens) < 3:
    raise ValueError("Invalid expression.")

  result = None
  op = None

  for token in tokens:
    if token in ("+", "-"):
      op = token
      continue

    dur = parse_duration(token)
    if dur:
      if result is None:
        result = dur
      else:
        return result + dur if op == "+" else result - dur
      continue

    dt = parse_datetime_safe(token)
    if dt:
      if result is None:
        result = dt
      else:
        if isinstance(result, datetime):
          if op == "-":
            return result - dt
          else:
            raise ValueError("Cannot add two dates.")
        elif isinstance(result, timedelta):
          if op == "+":
            return result + dt
          else:
            raise ValueError("Cannot subtract date from duration.")
      continue

    raise ValueError(f"Could not parse token: '{token}'")


# -----------------------
# Main Loop
# -----------------------
def get_prompt():
  return f"{Fore.LIGHTBLUE_EX}>>> {Style.RESET_ALL}"


def print_result(result):
  print(f"{Fore.LIGHTBLUE_EX}= {Style.RESET_ALL}{result}")


def print_error(result):
  print(f"{Fore.RED}! {Style.RESET_ALL}{result}")


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


def main():
  while True:
    try:
      user_input = input(get_prompt()).strip()
      if not user_input:
        continue

      answer = evaluate_expression(user_input)
      # answer maybe one of timedelta (dur +/- dur, dt - dt) or datetime (dt +/- dur)
      if isinstance(answer, datetime):
        print_result(answer.strftime("%Y-%m-%d %H:%M:%S"))
      elif isinstance(answer, timedelta):
        print_result(format_timedelta(answer))
    except (EOFError, KeyboardInterrupt):
      print("\n👋 Bye!")
      break
    except ValueError as e:
      print_error(f"Error: {e}")


if __name__ == "__main__":
  main()
