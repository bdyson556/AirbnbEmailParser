# tests/test_main.py
import unittest
import EmailParser
import sample_A
import sample_B
import sample_C
import sample_D
import logging

logging.basicConfig(level=logging.INFO)
TERMINAL_WIDTH = 400

class TestMainFunctions(unittest.TestCase):

    samples = [sample_A.input_data, sample_B.input_data, sample_C.input_data, sample_D.input_data]
    correct_data = [
        {"reservation_date": "2023-11-21T21:13:08", "guest_name": "Sheila Karpf",
          'guest_f_name': "Sheila", 'guest_l_name': "Karpf", "confirmation_code": "HMQTYNHWQD",
          "subject_line": "Reservation confirmed - Sheila Karpf arrives Jun 27", "unit": "condo_entire_unit",
          "check_in_date": "2024-06-27T17:00:00", "check_out_date": "2024-07-01T15:00:00", "guest_total": 545.62,
         "nightly_rate": 94.00, "nights": 4, "payout": 422.92, "cleaning_fee": 60.00, "guest_service_fee": 61.55,
         "host_service_fee": 13.08},
        {"reservation_date": "2023-11-18T00:11:43", "guest_name": "Ladisha Allen",
          'guest_f_name': "Ladisha", 'guest_l_name': "Allen", "confirmation_code": "HMHKX2M34Z",
          "subject_line": "Reservation confirmed - Ladisha Allen arrives Nov 19", "unit": "sheldon_guest_room",
          "check_in_date": "2023-11-19T17:00:00", "check_out_date": "2023-12-07T15:00:00", "guest_total": 732.36,
         "nightly_rate": 31.00, "nights": 18, "payout": 555.81, "cleaning_fee": 15.00, "guest_service_fee": 80.89,
         "host_service_fee": 17.19},
        {"reservation_date": "2024-02-16T13:30:36", "guest_name": "Rosie Chastain",
         'guest_f_name': "Rosie", 'guest_l_name': "Chastain", "confirmation_code": "HMWMZWW9CQ",
         "subject_line": "Reservation confirmed - Rosie Chastain arrives Feb 23", "unit": "condo_entire_unit",
         "check_in_date": "2024-02-23T17:00:00", "check_out_date": "2024-02-26T15:00:00", "guest_total": 327.98,
         "nightly_rate": 60.00, "nights": 3, "payout": 252.20, "cleaning_fee": 80.00, "guest_service_fee": 36.71,
         "host_service_fee": 7.80},
        {"reservation_date": "2024-02-12T03:59:36", "guest_name": "Fabian Gaspar",
         'guest_f_name': "Fabian", 'guest_l_name': "Gaspar", "confirmation_code": "HMY2FZY9SR",
         "subject_line": "Reservation confirmed - Fabian Gaspar arrives Jun 14", "unit": "condo_entire_unit",
         "check_in_date": "2024-06-14T17:00:00", "check_out_date": "2024-06-25T15:00:00", "guest_total": 1266.85,
         "nightly_rate": 84.03, "nights": 11, "payout": 974.17, "cleaning_fee": 80.00, "guest_service_fee": 141.78,
         "host_service_fee": 30.13}
    ]

    def test_samples(self):
        for i in range(0, len(self.samples)):
            msg = f"=====  TESTING INPUT {i+1} OF {len(self.samples)}: {self.samples[i]['name']}  "
            pad_length = max(0, TERMINAL_WIDTH - len(msg))
            logging.info(msg.ljust(pad_length, "="))
            output_data = EmailParser.main(self.samples[i])
            del output_data["body"]
            logging.info("\tCorrect data: " + str(self.correct_data[i]))
            logging.info("\tOutput data:  " + str(output_data))
            self.assertTrue(output_data == self.correct_data[i])
            logging.info("\tDATA EXTRACTION SUCCESSFUL.")

    def test_get_nightly_rate(self):
        rate_and_nights = EmailParser.find_rate_and_nights(sample_A.input_data["body_plain"])
        nightly_rate = EmailParser.find_nightly_rate(rate_and_nights)
        logging.info(f"Found nightly rate: {nightly_rate:.2f}")
        num_nights = EmailParser.find_num_nights(rate_and_nights)
        logging.info(f"Found num nights: {num_nights}")

    def test_get_cleaning_fee(self):
        cleaning_fee = EmailParser.find_fee(sample_A.input_data["body_plain"], "Cleaning fee")
        logging.info(f"Found cleaning fee: {cleaning_fee:.2f}")
        cleaning_fee = EmailParser.find_fee(sample_B.input_data["body_plain"], "Cleaning fee")
        logging.info(f"Found cleaning fee: {cleaning_fee:.2f}")

    def test_get_guest_service_fee(self):
        cleaning_fee = EmailParser.find_fee(sample_A.input_data["body_plain"], "Guest service fee")
        logging.info(f"Found guest service fee: {cleaning_fee:.2f}")

    def test_get_host_service_fee(self):
        cleaning_fee = EmailParser.find_fee(sample_A.input_data["body_plain"], "Service fee")
        logging.info(f"Found host service fee: {cleaning_fee:.2f}")

    def test_find_all_totals(self):
        totals = EmailParser.find_totals(sample_A.input_data["body_plain"])
        logging.info(f"Found totals: {totals}")
        guest_total = EmailParser.get_guest_total(totals)
        logging.info(f"Found guest total: {guest_total}")
        self.assertEqual(guest_total, 545.62)
        payout = EmailParser.get_payout(totals)
        logging.info(f"Found payout: {payout}")
        self.assertEqual(payout, 422.92)

    def test_get_guest_total(self):
        totals = EmailParser.find_totals(sample_A.input_data["body_plain"])

    def test_get_payout(self):
        totals = EmailParser.find_totals(sample_A.input_data["body_plain"])


if __name__ == '__main__':
    unittest.main()
    # pass