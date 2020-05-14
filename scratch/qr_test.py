import sys

import qrcode

URLS = """
https://keybase.io/warp/warp_1.0.9_SHA256_a2067491ab582bde779f4505055807c2479354633a2216b22cf1e92d1a6e4a87.html
https://en.wikipedia.org/wiki/Reed%E2%80%93Solomon_error_correction#Systematic_encoding_procedure:_The_message_as_an_initial_sequence_of_values
https://www.youtube.com/watch?v=TrB62cPPNxc
"""


def main(args=sys.argv[1:]):
    for url in URLS.strip().splitlines():
        qr = qrcode.QRCode(
            version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4,
        )

        qr.add_data(url.encode("ascii"))
        print(url)
        qr.print_ascii(invert=True)


if __name__ == '__main__':
    main()
