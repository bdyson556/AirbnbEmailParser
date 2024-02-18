import re

def extract_name_and_date(subject):
    pattern = r'Reservation confirmed - (\w+\s\w+) arrives (\w+\s\d+)'
    match = re.search(pattern, subject)

    if match:
        name = match.group(1)
        date = match.group(2)
        return name, date

    return None, None
