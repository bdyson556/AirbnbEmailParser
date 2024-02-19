# To be used as a Zapier function in a zap that scrapes a new email from Gmail for reservation data and creates a record
# in DynamoDB. Zapier provides dictionary 'input_data' as input, which I am pre-populating with 'subject_line',
# 'body_plain', and 'date'. The sample data imitates this format. The output is a dicionary.

# NOTE: You must un-comment the return statement at the end before using in Zapier.

import re
import sys
import traceback
from datetime import datetime
import logging

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# log lower levels to stdout
stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.addFilter(lambda rec: rec.levelno <= logging.INFO)
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)

# log higher levels to stderr (red)
stderr_handler = logging.StreamHandler(stream=sys.stderr)
stderr_handler.addFilter(lambda rec: rec.levelno > logging.INFO)
stderr_handler.setFormatter(formatter)
logger.addHandler(stderr_handler)

UTC_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"
DOLLAR_PATTERN_NO_COMMA = fr"\d{{1,3}}\.\d{{2}}"
DOLLAR_PATTERN_WITH_COMMA = fr"\$\d{{1,3}}(?:,\d{{3}})*\.\d{{2}}"
DOLLAR_PATTERN_WITH_COMMA_NO_DOLLAR = fr"\d{{1,3}}(?:,\d{{3}})*\.\d{{2}}"
NUM_NIGHTS_PATTERN = r"\d{1,2}"
CHECKIN_PATTERN = "check.{0,10}in"
CHECKOUT_PATTERN = "check.{0,10}out"
DATE_PATTERN = "(?:SUN|MON|TUE|WED|THU|FRI|SAT|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY).{0,5}(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|JANUARY|FEBRUARY|MARCH|APRIL|AUGUST|SEPTEMBER|NOVEMBER|DECEMBER).{0,5}\d{1,4}"
ANY_OF_THREE = f'(?:{CHECKOUT_PATTERN}|{CHECKIN_PATTERN}|{DATE_PATTERN})'
CHECKIN_CHECKOUT_PATTERN = fr"(?:{ANY_OF_THREE}.{{0,100}}){{2,8}}"
FEE_PATTERN = fr".{{0,50}}\$\d{{2,3}}\.\d{{2}}\b"
DATE_FORMATS_WITH_YEAR = [
    "%a, %b %d, %Y",
    "%A, %B %d, %Y",
    "%a, %d %b %Y %H:%M:%S %z (%Z)"
]
DATE_FORMATS_WITHOUT_YEAR = ["%a, %b %d", "%A, %B %d"]
CURRENT_YEAR = datetime.now().year
CONDO_ROOM_A_LIST_NAME, rm_A_output_nm = "FRESH UPTOWN CONDO ROOM WITH PRIVATE PARKING", "condo_room_A"
CONDO_ROOM_B_LIST_NAME, rm_B_output_nm = "NEWLY REMODELED POSH UPTOWN CONDO ROOM", "condo_room_B"
CONDO_ENTIRE_UNIT_LIST_NAME, condo_unit_output_nm = "TWO-BEDROOM UPTOWN CONDO WITH BIDET", "condo_entire_unit"
SHELDON_GUEST_ROOM_LIST_NAME, sheldon_guest_rm_output_nm = "GUEST SUITE WITH PRIVATE BATH", "sheldon_guest_room"

current_errors = []


def main(input_data):
    body = input_data['body_plain'].replace("\n", "  ")
    subject_line = input_data["subject_line"]
    sent_datetime = convert_to_iso_date(input_data['date'])
    year = sent_datetime.year
    sent_datetime = sent_datetime.strftime(UTC_ISO_FORMAT)

    confirmation_code = find_confirmation_code(body)

    dates = find_dates(body, year)
    iso_checkin, iso_checkout = dates[0], dates[1]

    guest_names = find_guest_names(subject_line)
    guest_name, guest_f_name, guest_l_name = guest_names[0], guest_names[1], guest_names[2]

    unit = find_unit(body)

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
        'nightly_rate': nightly_rate,
        'nights': nights,
        'payout': payout,
        'cleaning_fee': cleaning_fee,
        'guest_service_fee': guest_service_fee,
        'host_service_fee': host_service_fee,
        'body': body,
        'errors': current_errors
    }


def find_confirmation_code(body):
    confirmation_search_result = re.findall(r"\bHM[A-Z0-9]{8,12}\b", body)
    if len(confirmation_search_result) == 0:
        err = RuntimeError("Confirmation code not found.")
        current_errors.append(err)
        raise err
    return confirmation_search_result[0]


def find_dates(body, year):
    rough_search_result = re.findall(CHECKIN_CHECKOUT_PATTERN, body, re.IGNORECASE)
    iso_dates = []
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
        iso_checkin = iso_dates[0].replace(hour=17).strftime(UTC_ISO_FORMAT)  # Set check-in time to 5:00
        iso_checkout = iso_dates[1].replace(hour=15).strftime(UTC_ISO_FORMAT)  # Set check-in time to 3:00
        return [iso_checkin, iso_checkout]
    except Exception as e:
        traceback.print_exc()


def convert_to_iso_date(date_string, year=None):
    try:
        date = try_date_formats_with_year(date_string)
        if date: return date
    except: pass
    try:
        date = try_date_formats_without_year(date_string, year)
        if date: return date
    except: pass
    try:
        date_string += ", 2000"
        date = try_date_formats_with_year(date_string)
        if date:
            date = date.replace(year=year)
            return date
    except:
        err = RuntimeError("Failed to convert date string to ISO date. String: " + str(date_string) +
                           ". Date formats attempted: " + str(DATE_FORMATS_WITHOUT_YEAR) + " " + str(
            DATE_FORMATS_WITH_YEAR))
        current_errors.append(err)
        raise err


def try_date_formats_with_year(date_string):
    for date_format in DATE_FORMATS_WITH_YEAR:
        try:
            date = datetime.strptime(date_string, date_format)
            return date
        except:
            logger.warning(f"Failed to parse date '{date_string}' with date format '{date_format}'.")


def try_date_formats_without_year(date_string, year):
    for date_format in DATE_FORMATS_WITHOUT_YEAR:
        try:
            date = datetime.strptime(date_string, date_format)
            date = date.replace(year=year)
            return date
        except:
            logger.warning(f"Failed to parse date '{date_string}' with date format '{date_format}'.")


def find_rate_and_nights(body):
    pattern = fr"{DOLLAR_PATTERN_NO_COMMA} x {NUM_NIGHTS_PATTERN} nights"
    match = re.search(pattern, body)
    if match:
        return match.group()
    else:
        err = RuntimeError("Nightly rate not found!")
        current_errors.append(err)
        raise err


def find_nightly_rate(rate_and_nights):
    # e.g. "$94.00 x 4 nights"
    try:
        return float(re.search(DOLLAR_PATTERN_NO_COMMA, rate_and_nights).group())
    except:
        err = RuntimeError(f"Unable to convert nightly rate to float. Rate: {rate_and_nights}.")
        current_errors.append(err)
        raise err


def find_num_nights(rate_and_nights):
    pre_result = re.search(f"{NUM_NIGHTS_PATTERN} nights", rate_and_nights).group()
    try:
        return int(re.search(NUM_NIGHTS_PATTERN, pre_result).group())
    except:
        err = RuntimeError("Unable to return num nights as int.")
        current_errors.append(err)
        raise err


def find_fee(body, fee):
    # e.g. "Cleaning fee   $60.00"
    pattern = fr"{fee}{FEE_PATTERN}"
    pre_result = re.search(pattern, body)
    if pre_result:
        try:
            pattern = fr"{DOLLAR_PATTERN_NO_COMMA}"
            return float(re.findall(pattern, pre_result.group(0))[0])
        except:
            err = RuntimeError(f"Unable to convert {fee} to float.")
            current_errors.append(err)
            raise err


def find_totals(body):
    pattern = fr"TOTAL.{{0,12}}? {DOLLAR_PATTERN_WITH_COMMA}"
    raw_search_result = re.findall(pattern, body)
    if len(raw_search_result) < 2:
        err = RuntimeError("Fewer than two totals found.")
        current_errors.append(err)
        raise err
    try:
        # Extract dollar amounts as floats.
        return list(map(lambda x: float(re.search(DOLLAR_PATTERN_WITH_COMMA_NO_DOLLAR, x).group().replace(",", "")),
                        raw_search_result))
    except:
        err = RuntimeError("Unable to extract totals as floats.")
        current_errors.append(err)
        raise err


def get_payout(totals): return min(totals)


def get_guest_total(totals): return max(totals)


def find_guest_names(subject_line):
    pattern = re.compile(r'[\w\s]* arrives', re.U)
    name_rough_search = list(map(lambda x: x.strip(), re.findall(pattern, subject_line)))
    names = []
    try:
        guest_name = name_rough_search[0].replace(" arrives", "")
        guest_names = guest_name.split(" ")
        guest_f_name = guest_names[0]
        names = [guest_name, guest_f_name]
    except Exception as e:
        current_errors.append(e)
        raise RuntimeError(e)
    if len(guest_names) > 1: guest_l_name = guest_names[1]; names.append(guest_l_name)

    return names


def find_unit(body):
    if CONDO_ENTIRE_UNIT_LIST_NAME in body:
        return condo_unit_output_nm
    elif SHELDON_GUEST_ROOM_LIST_NAME in body:
        return sheldon_guest_rm_output_nm
    elif CONDO_ROOM_A_LIST_NAME in body:
        return rm_A_output_nm
    elif CONDO_ROOM_B_LIST_NAME in body:
        return rm_B_output_nm
    else:
        return "INVALID_UNIT"


# return main(input_data)
