import re
from datetime import datetime, date, timedelta
from typing import Optional, Union
import calendar

class FlexibleDateParser:
    """Parse flexible date inputs and convert them to standard ISO format (YYYY-MM-DD)"""
    
    def __init__(self):
        self.today = date.today()
        
        # Month name mappings
        self.month_names = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
            'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        # Ordinal number mappings
        self.ordinals = {
            '1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5, '6th': 6, '7th': 7,
            '8th': 8, '9th': 9, '10th': 10, '11th': 11, '12th': 12, '13th': 13,
            '14th': 14, '15th': 15, '16th': 16, '17th': 17, '18th': 18, '19th': 19,
            '20th': 20, '21st': 21, '22nd': 22, '23rd': 23, '24th': 24, '25th': 25,
            '26th': 26, '27th': 27, '28th': 28, '29th': 29, '30th': 30, '31st': 31
        }

    def parse_date(self, date_input: str) -> str:
        """
        Parse flexible date input and return ISO format date (YYYY-MM-DD)
        """
        if not date_input:
            return self.today.isoformat()
            
        date_input = date_input.strip().lower()
        
        # Handle relative dates
        if date_input in ['today', 'now']:
            return self.today.isoformat()
        elif date_input in ['tomorrow', 'next day']:
            return (self.today + timedelta(days=1)).isoformat()
        elif date_input == 'yesterday':
            return (self.today - timedelta(days=1)).isoformat()
        elif date_input in ['this week', 'end of this week']:
            return self._get_end_of_week().isoformat()
        elif date_input in ['next week', 'end of next week']:
            return self._get_end_of_next_week().isoformat()
        elif date_input in ['this month', 'end of this month', 'end of month']:
            return self._get_end_of_month().isoformat()
        elif date_input in ['next month', 'end of next month']:
            return self._get_end_of_next_month().isoformat()
        
        # Handle "next X days" pattern
        next_days_match = re.search(r'next (\d+) days?', date_input)
        if next_days_match:
            days = int(next_days_match.group(1))
            return (self.today + timedelta(days=days)).isoformat()
        
        # Handle "in X days" pattern
        in_days_match = re.search(r'in (\d+) days?', date_input)
        if in_days_match:
            days = int(in_days_match.group(1))
            return (self.today + timedelta(days=days)).isoformat()
        
        # Try to parse as ISO format (YYYY-MM-DD)
        iso_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', date_input)
        if iso_match:
            year, month, day = map(int, iso_match.groups())
            try:
                parsed_date = date(year, month, day)
                return parsed_date.isoformat()
            except ValueError:
                pass
        
        # Try to parse formats like "April 1, 2025" or "April 1 2025"
        month_day_year_match = re.search(r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', date_input)
        if month_day_year_match:
            month_str, day_str, year_str = month_day_year_match.groups()
            month = self.month_names.get(month_str.lower())
            if month:
                try:
                    parsed_date = date(int(year_str), month, int(day_str))
                    return parsed_date.isoformat()
                except ValueError:
                    pass
        
        # Try to parse formats like "1st April 2025" or "1 April 2025"
        day_month_year_match = re.search(r'(\d{1,2}(?:st|nd|rd|th)?)\s+(\w+)\s+(\d{4})', date_input)
        if day_month_year_match:
            day_str, month_str, year_str = day_month_year_match.groups()
            
            # Handle ordinal numbers
            day = self.ordinals.get(day_str) or int(re.sub(r'[^\d]', '', day_str))
            month = self.month_names.get(month_str.lower())
            
            if month:
                try:
                    parsed_date = date(int(year_str), month, day)
                    return parsed_date.isoformat()
                except ValueError:
                    pass
        
        # Try to parse DD/MM/YYYY or MM/DD/YYYY
        slash_match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_input)
        if slash_match:
            part1, part2, year = map(int, slash_match.groups())
            # Try DD/MM/YYYY first (European format)
            try:
                parsed_date = date(year, part2, part1)
                return parsed_date.isoformat()
            except ValueError:
                # Try MM/DD/YYYY (American format)
                try:
                    parsed_date = date(year, part1, part2)
                    return parsed_date.isoformat()
                except ValueError:
                    pass
        
        # Try to parse DD-MM-YYYY or MM-DD-YYYY
        dash_match = re.match(r'(\d{1,2})-(\d{1,2})-(\d{4})', date_input)
        if dash_match:
            part1, part2, year = map(int, dash_match.groups())
            # Try DD-MM-YYYY first (European format)
            try:
                parsed_date = date(year, part2, part1)
                return parsed_date.isoformat()
            except ValueError:
                # Try MM-DD-YYYY (American format)
                try:
                    parsed_date = date(year, part1, part2)
                    return parsed_date.isoformat()
                except ValueError:
                    pass
        
        # If all parsing fails, return today's date as fallback
        return self.today.isoformat()
    
    def _get_end_of_week(self) -> date:
        """Get the end of current week (Sunday)"""
        days_ahead = 6 - self.today.weekday()  # Sunday is 6
        return self.today + timedelta(days=days_ahead)
    
    def _get_end_of_next_week(self) -> date:
        """Get the end of next week (Sunday)"""
        return self._get_end_of_week() + timedelta(days=7)
    
    def _get_end_of_month(self) -> date:
        """Get the last day of current month"""
        last_day = calendar.monthrange(self.today.year, self.today.month)[1]
        return date(self.today.year, self.today.month, last_day)
    
    def _get_end_of_next_month(self) -> date:
        """Get the last day of next month"""
        if self.today.month == 12:
            next_year = self.today.year + 1
            next_month = 1
        else:
            next_year = self.today.year
            next_month = self.today.month + 1
        
        last_day = calendar.monthrange(next_year, next_month)[1]
        return date(next_year, next_month, last_day)
    
    def parse_date_range(self, date_input: str) -> tuple[str, str]:
        """
        Parse date range inputs like 'this week', 'next 7 days', etc.
        Returns (start_date, end_date) in ISO format
        """
        date_input = date_input.strip().lower()
        
        if date_input in ['this week']:
            start = self.today - timedelta(days=self.today.weekday())  # Monday
            end = self._get_end_of_week()  # Sunday
            return start.isoformat(), end.isoformat()
        
        elif date_input in ['next week']:
            next_monday = self.today + timedelta(days=(7 - self.today.weekday()))
            next_sunday = next_monday + timedelta(days=6)
            return next_monday.isoformat(), next_sunday.isoformat()
        
        elif date_input in ['this month']:
            start = date(self.today.year, self.today.month, 1)
            end = self._get_end_of_month()
            return start.isoformat(), end.isoformat()
        
        elif date_input in ['next month']:
            if self.today.month == 12:
                next_year = self.today.year + 1
                next_month = 1
            else:
                next_year = self.today.year
                next_month = self.today.month + 1
            
            start = date(next_year, next_month, 1)
            end = self._get_end_of_next_month()
            return start.isoformat(), end.isoformat()
        
        # Handle "next X days" pattern
        next_days_match = re.search(r'next (\d+) days?', date_input)
        if next_days_match:
            days = int(next_days_match.group(1))
            start = self.today
            end = self.today + timedelta(days=days)
            return start.isoformat(), end.isoformat()
        
        # Default to single date
        parsed_date = self.parse_date(date_input)
        return parsed_date, parsed_date
