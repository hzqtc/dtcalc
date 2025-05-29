# 🕒 Date & Time CLI Calculator

A powerful, interactive command-line tool for performing natural and flexible date/time arithmetic — with support for mixed durations, multiple date/time formats, and colorful prompts.

---

## ✨ Features

- ✅ Add or subtract **dates**, **times**, **datetimes**, and **durations**
- 🧠 Accepts multiple input formats:
  - `2024-01-10`
  - `June/24/2023`
  - `06/10/24 15:33`
- 🗓️ Supports complex durations:
  - `2years 3days`
  - `1y6mo10d`
  - `5w3d2h`
- 💻 Take expression from argument or stdin
  - `dtcalc "today + 100d"`
  - `echo "now + 8h" | dtcalc`
- ⌨️ Interactive prompt with:
  - Command history navigation (↑ / ↓)
  - Persistent history across sessions

---

## 🚀 Setup

### 1. Clone the repo

```bash
git clone https://github.com/hzqtc/dtcalc
cd dtcalc
```

### 2. Install dependencies
```bash
uv sync
```

### 3. Run
```bash
uv run src/dtcalc.py
```

## 🧪 Examples

```
> today + 10 days
= 2025-06-04

> now + 10 hours
= 2025-05-25 23:24:58

> 2024-07-10 + 300 days
= 2025-05-06

> 2024-07-10 - 2023-07-10
= 366 days

> 11days + 2weeks3days
= 28 days

> 06/10/24 15:33 + 10d5h
= 2024-06-20 20:33:00
```

