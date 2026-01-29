"""CRON expression parsing utilities."""

from datetime import datetime

from croniter import croniter

from codegeass.core.exceptions import ValidationError


class CronParser:
    """Utility class for CRON expression operations."""

    # Common CRON expression patterns
    PATTERNS = {
        "@yearly": "0 0 1 1 *",
        "@annually": "0 0 1 1 *",
        "@monthly": "0 0 1 * *",
        "@weekly": "0 0 * * 0",
        "@daily": "0 0 * * *",
        "@midnight": "0 0 * * *",
        "@hourly": "0 * * * *",
    }

    @classmethod
    def normalize(cls, expression: str) -> str:
        """Normalize CRON expression, expanding aliases."""
        return cls.PATTERNS.get(expression.lower(), expression)

    @classmethod
    def validate(cls, expression: str) -> bool:
        """Validate a CRON expression."""
        normalized = cls.normalize(expression)
        try:
            croniter(normalized)
            return True
        except (ValueError, KeyError):
            return False

    @classmethod
    def get_next(cls, expression: str, base_time: datetime | None = None) -> datetime:
        """Get next scheduled time."""
        normalized = cls.normalize(expression)
        if not cls.validate(normalized):
            raise ValidationError(f"Invalid CRON expression: {expression}")

        base = base_time or datetime.now()
        cron = croniter(normalized, base)
        return cron.get_next(datetime)

    @classmethod
    def get_prev(cls, expression: str, base_time: datetime | None = None) -> datetime:
        """Get previous scheduled time."""
        normalized = cls.normalize(expression)
        if not cls.validate(normalized):
            raise ValidationError(f"Invalid CRON expression: {expression}")

        base = base_time or datetime.now()
        cron = croniter(normalized, base)
        return cron.get_prev(datetime)

    @classmethod
    def is_due(cls, expression: str, window_seconds: int = 60) -> bool:
        """Check if expression is due within the time window."""
        normalized = cls.normalize(expression)
        now = datetime.now()
        prev = cls.get_prev(normalized, now)
        return (now - prev).total_seconds() <= window_seconds

    @classmethod
    def get_next_n(
        cls, expression: str, n: int, base_time: datetime | None = None
    ) -> list[datetime]:
        """Get next N scheduled times."""
        normalized = cls.normalize(expression)
        if not cls.validate(normalized):
            raise ValidationError(f"Invalid CRON expression: {expression}")

        base = base_time or datetime.now()
        cron = croniter(normalized, base)
        return [cron.get_next(datetime) for _ in range(n)]

    @classmethod
    def describe(cls, expression: str) -> str:
        """Get human-readable description of schedule."""
        normalized = cls.normalize(expression)

        # Check for aliases first
        for alias, pattern in cls.PATTERNS.items():
            if expression.lower() == alias:
                return alias.replace("@", "").capitalize()

        if not cls.validate(normalized):
            return "Invalid expression"

        parts = normalized.split()
        if len(parts) != 5:
            return normalized

        minute, hour, dom, month, dow = parts

        # Common patterns
        if normalized == "* * * * *":
            return "Every minute"
        if normalized == "0 * * * *":
            return "Every hour"
        if normalized == "0 0 * * *":
            return "Daily at midnight"

        if minute != "*" and hour == "*" and dom == "*" and month == "*" and dow == "*":
            return f"Every hour at minute {minute}"

        if minute != "*" and hour != "*" and dom == "*" and month == "*" and dow == "*":
            return f"Daily at {hour.zfill(2)}:{minute.zfill(2)}"

        if minute != "*" and hour != "*" and dow != "*" and dom == "*" and month == "*":
            day_names = {
                "0": "Sunday",
                "1": "Monday",
                "2": "Tuesday",
                "3": "Wednesday",
                "4": "Thursday",
                "5": "Friday",
                "6": "Saturday",
                "1-5": "weekdays",
                "0,6": "weekends",
            }
            day_str = day_names.get(dow, f"day {dow}")
            return f"At {hour.zfill(2)}:{minute.zfill(2)} on {day_str}"

        return normalized

    @classmethod
    def parse_field(cls, field: str, min_val: int, max_val: int) -> list[int]:
        """Parse a single CRON field into list of values."""
        values: set[int] = set()

        for part in field.split(","):
            if part == "*":
                values.update(range(min_val, max_val + 1))
            elif "-" in part:
                if "/" in part:
                    range_part, step = part.split("/")
                    start, end = map(int, range_part.split("-"))
                    values.update(range(start, end + 1, int(step)))
                else:
                    start, end = map(int, part.split("-"))
                    values.update(range(start, end + 1))
            elif "/" in part:
                base, step = part.split("/")
                if base == "*":
                    values.update(range(min_val, max_val + 1, int(step)))
                else:
                    values.update(range(int(base), max_val + 1, int(step)))
            else:
                values.add(int(part))

        return sorted(values)
