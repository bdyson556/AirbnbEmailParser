# tests/test_main.py

import unittest
import EmailParser
import sample_A
import sample_B
import logging

logging.basicConfig(level=logging.INFO)

class TestMainFunctions(unittest.TestCase):

    samples = [sample_A.input_data, sample_B.input_data]
    correct_data = [
        {"reservation_date": "2023-11-21T21:13:08", "guest_name": "Sheila Karpf",
          'guest_f_name': "Sheila", 'guest_l_name': "Karpf", "confirmation_code": "HMQTYNHWQD",
          "subject_line": "Reservation confirmed - Sheila Karpf arrives Jun 27", "unit": "condo_entire_unit",
          "check_in_date": "2024-06-27T17:00:00", "check_out_date": "2024-07-01T15:00:00", "guest_total": 545.62},
        {"reservation_date": "2023-11-18T00:11:43", "guest_name": "Ladisha Allen",
          'guest_f_name': "Ladisha", 'guest_l_name': "Allen", "confirmation_code": "HMHKX2M34Z",
          "subject_line": "Reservation confirmed - Ladisha Allen arrives Nov 19", "unit": "sheldon_guest_room",
          "check_in_date": "2023-11-19T17:00:00", "check_out_date": "2023-12-07T15:00:00", "guest_total": 732.36}
    ]



    def test_samples(self):
        # for sample in self.samples:
        for i in range(0, len(self.samples)):
            output_data = EmailParser.main(self.samples[i])
            del output_data["body"]
            logging.info("Correct data: " + str(self.correct_data[i]))
            logging.info("Output data:  " + str(output_data))
            self.assertTrue(output_data == self.correct_data[i])


if __name__ == '__main__':
    unittest.main()
    # pass