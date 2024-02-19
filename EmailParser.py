import re
import traceback
from datetime import datetime
import logging

DOLLAR_PATTERN_NO_COMMA = "\$\d{2,3}\.\d{2}"
DOLLAR_PATTERN_WITH_COMMA = "\$\d{1,3}(?:,\d{3})*\.\d{2}"
CHECKIN_PATTERN = "check.{0,10}in"
CHECKOUT_PATTERN = "check.{0,10}out"
DATE_PATTERN = "(?:SUN|MON|TUE|WED|THU|FRI|SAT|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY).{0,5}(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|JANUARY|FEBRUARY|MARCH|APRIL|AUGUST|SEPTEMBER|NOVEMBER|DECEMBER).{0,5}\d{1,4}"
ANY_OF_THREE = f'(?:{CHECKOUT_PATTERN}|{CHECKIN_PATTERN}|{DATE_PATTERN})'
CHECKIN_CHECKOUT_PATTERN = rf"(?:{ANY_OF_THREE}.{{0,100}}){{2,8}}"
DATE_FORMATS_WITH_YEAR = [
    "%a, %b %d, %Y",
    "%A, %B %d, %Y",
    "%a, %d %b %Y %H:%M:%S %z (%Z)"
]
DATE_FORMATS_WITHOUT_YEAR = ["%a, %b %d", "%A, %B %d"]
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"
CURRENT_YEAR = datetime.now().year
CONDO_ROOM_A = "FRESH UPTOWN CONDO ROOM WITH PRIVATE PARKING"
CONDO_ROOM_B = "NEWLY REMODELED POSH UPTOWN CONDO ROOM"
CONDO_ENTIRE_UNIT = "TWO-BEDROOM UPTOWN CONDO WITH BIDET"
SHELDON_GUEST_ROOM = "GUEST SUITE WITH PRIVATE BATH"
CONFIRMATION_PATTERN = r"\bHM[A-Z0-9]{8,12}\b"


def convert_to_iso_date(date_string, year=None):
    for date_format in DATE_FORMATS_WITH_YEAR:
        try:
            date = datetime.strptime(date_string, date_format)
            return date
        except:
            logging.warning(f"Failed to parse date '{date_string}' with date format '{date_format}'.")
    for date_format in DATE_FORMATS_WITHOUT_YEAR:
        try:
            date = datetime.strptime(date_string, date_format)
            date = date.replace(year=year)
            return date
        except:
            logging.warning(f"Failed to parse date '{date_string}' with date format '{date_format}'.")
    raise RuntimeError("Failed to convert date string to ISO date. String: " + str(date_string) +
                       "Date formats attempted: " + str(DATE_FORMATS_WITHOUT_YEAR) + " " + str(DATE_FORMATS_WITH_YEAR))


def find_rate_and_nights(body):
    match = re.search("\$\d{2,3}\.\d{2} x \d{1,2} nights", body)
    if match:
        return match.group()
    else:
        raise RuntimeError("Nightly rate not found!")


def find_nightly_rate(rate_and_nights):
    # e.g. "$94.00 x 4 nights"
    try:
        return float(re.search("\d{2,3}\.\d{2}", rate_and_nights).group())
    except:
        raise RuntimeError(f"Unable to convert nightly rate to float. Rate: {rate_and_nights}.")


def find_num_nights(rate_and_nights):
    # e.g. "$94.00 x 4 nights"
    pre_result = re.search("\d{1,2} nights", rate_and_nights).group()
    return int(re.search("\d{1,2}", pre_result).group())


def find_fee(body, fee):
    # e.g. "Cleaning fee   $60.00"
    pattern = fee + ".{0,50}\$\d{2,3}\.\d{2}\s"
    pre_result = re.search(pattern, body)
    if pre_result:
        try:
            return float(re.findall("\d{1,3}\.\d{2}", pre_result.group(0))[0])
        except:
            raise RuntimeError(f"Unable to convert {fee} to float.")


def find_totals(body):
    pattern = "TOTAL.{0,12}? \$\d{1,3}(?:,\d{3})*\.\d{2}"
    raw_search_result = re.findall(pattern, body)
    if len(raw_search_result) < 2:
        raise RuntimeError("Fewer than two totals found.")
    try:
        # Extract dollar amounts as floats.
        return list(map(lambda x: float(re.search("\d{1,3}(?:,\d{3})*\.\d{2}", x).group().replace(",", "")), raw_search_result))
    except:
        raise RuntimeError("Unable to extract totals as floats.")


def get_payout(totals):
    return min(totals)

def get_guest_total(totals):
    return max(totals)

def main(input_data):
    body = input_data['body_plain'].replace("\n", "  ")
    subject_line = input_data["subject_line"]
    sent_datetime = convert_to_iso_date(input_data['date'])
    year = sent_datetime.year
    sent_datetime = sent_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    confirmation_search_result = re.findall(CONFIRMATION_PATTERN, body)
    iso_dates = []
    iso_checkin = None
    iso_checkout = None
    guest_name = None
    guest_f_name = None
    guest_l_name = None
    unit = None

    try:
        if len(confirmation_search_result) == 0: raise Exception("Confirmation code not found.")
        confirmation_code = confirmation_search_result[0]
    except Exception:
        traceback.print_exc()

    # Find dates

    rough_search_result = re.findall(CHECKIN_CHECKOUT_PATTERN, body, re.IGNORECASE)

    try:
        if len(rough_search_result) == 0:
            raise Exception("Checkin/checkout date pattern not found.")
        elif len(rough_search_result) != 1:
            raise Exception("Multiple matches found for checkin/checkout date pattern.")
        fine_search_result = re.findall(rf"{DATE_PATTERN}", rough_search_result[0], re.IGNORECASE)

        for date in fine_search_result:
            try:
                iso_date = convert_to_iso_date(date, year)
                iso_dates.append(iso_date)
            except ValueError as e:
                traceback.print_exc()
        iso_dates.sort()
        iso_checkin = iso_dates[0].replace(hour=17).strftime(ISO_FORMAT)  # Set check-in time to 5:00
        iso_checkout = iso_dates[1].replace(hour=15).strftime(ISO_FORMAT)  # Set check-in time to 3:00
    except Exception as e:
        traceback.print_exc()

    # Find guest name

    name_rough_search = re.findall(r"[A-Za-z0-9]+[\s]*[A-Za-z0-9]* arrives", subject_line)
    try:
        guest_name = name_rough_search[0].replace(" arrives", "")
        guest_names = guest_name.split(" ")
        guest_f_name = guest_names[0]
    except Exception as e:
        traceback.print_exc()
    if len(guest_names) > 1: guest_l_name = guest_names[1]

    # Find unit

    if CONDO_ENTIRE_UNIT in body:
        unit = "condo_entire_unit"
    elif CONDO_ROOM_A in body:
        unit = "condo_room_A"
    elif CONDO_ROOM_B in body:
        unit = "condo_room_B"
    elif SHELDON_GUEST_ROOM in body:
        unit = "sheldon_guest_room"
    else:
        unit = "INVALID_UNIT"

    # Find guest payment

    # pmt_pattern = r"\$\d+(?:\.\d{2})?\b"
    # pmt_search_result = re.findall(pmt_pattern, body)
    # try:
    #     if len(pmt_search_result) == 0: raise RuntimeError("Guest payment not found.")
    #     dollar_signs_removed = [amount.replace('$', '') for amount in pmt_search_result]
    #     float_payments = map(lambda x: float(x), dollar_signs_removed)
    #     guest_total = max(float_payments)
    # except:
    #     traceback.print_exc()

    totals = find_totals(body)
    payout = get_payout(totals)
    guest_total = get_guest_total(totals)
    rate_and_nights = find_rate_and_nights(body)
    nightly_rate = find_nightly_rate(rate_and_nights)
    nights = find_num_nights(rate_and_nights)
    cleaning_fee = find_fee(body, "Cleaning fee")
    guest_service_fee = find_fee(body, "Guest service fee")
    host_service_fee = find_fee(body, "Service fee")

    return {
        'reservation_date': sent_datetime,
        'guest_name': guest_name,
        'guest_f_name': guest_f_name,
        'guest_l_name': guest_l_name,
        'confirmation_code': confirmation_code,
        'subject_line': subject_line,
        'unit': unit,
        'check_in_date': iso_checkin,
        'check_out_date': iso_checkout,
        'guest_total': guest_total,
        'nightly_rate':  nightly_rate,
        'nights': nights,
        'payout': payout,
        'cleaning_fee': cleaning_fee,
        'guest_service_fee': guest_service_fee,
        'host_service_fee': host_service_fee,
        'body': body
    }

# return main(input_data)