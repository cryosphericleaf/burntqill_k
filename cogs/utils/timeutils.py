import datetime
from typing import Dict
import re
import datetime

from typing import Any, Iterable, Optional, Sequence

class Timeconverter:

    def parse_time(input_time: str) -> int:
        time_units: Dict[str, str] = {
            'years': r'(\d+)\s*(?:year|yr|yrs|y)',
            'months': r'(\d+)\s*(?:month|mo|mos|mon|months)',
            'weeks': r'(\d+)\s*(?:week|wk|wks|weeks)',
            'days': r'(\d+)\s*(?:day|d|days)',
            'hours': r'(\d+)\s*(?:hour|hr|hrs|hours|h)',
            'minutes': r'(\d+)\s*(?:minute|min|mins|minutes|mi|m)',
            'seconds': r'(\d+)\s*(?:second|sec|secs|seconds|s)',
        }

        total_seconds: int = 0

        for unit, pattern in time_units.items():
            match = re.search(pattern, input_time)
            if match:
                value: int = int(match.group(1))
                if unit in ['months', 'years']:
                    if unit == 'months':
                        value *= int(30.44 * 24 * 3600)  # Average days per month
                    else:
                        value *= int(365.25 * 24 * 3600)  # Average days per year
                else:
                    if unit == 'weeks':
                        value *= int(7 * 24 * 3600)  # Convert weeks to seconds
                    else:
                        value *= {
                            'days': int(24 * 3600),
                            'hours': int(3600),
                            'minutes': int(60),
                            'seconds': int(1),
                        }[unit]  # Convert other units to seconds
                total_seconds += value

        return total_seconds


    @staticmethod
    def seconds_to_relative(seconds: int) -> str:
        """
        Convert seconds to Discord relative timestamp.

        Parameters:
        seconds (int): The seconds to be converted.

        Returns:
        str: The Discord relative timestamp.
        """
        return f'<t:{int(datetime.datetime.now().timestamp() + seconds)}:R>'

    def format_dt(dt: datetime.datetime, style: Optional[str] = None) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)

        if style is None:
            return f'<t:{int(dt.timestamp())}>'
        return f'<t:{int(dt.timestamp())}:{style}>'
