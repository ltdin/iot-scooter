import qrcode


def create_qr_code():
    """
    Create a simple QR code for testing.

    The QR only contains the unlock_code, for example:
    BK-NEDJCNKDBDBM

    This is easier for the Raspberry Pi camera to scan than a long JSON QR.
    """

    unlock_code = input("Enter unlock_code from booking response: ").strip()

    if not unlock_code:
        print("unlock_code is required.")
        return

    if not unlock_code.startswith("BK-"):
        print("Invalid unlock_code. It should start with BK-")
        return

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=16,
        border=6,
    )

    qr.add_data(unlock_code)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    image.save("customer_unlock_qr.png")

    print("QR code created: customer_unlock_qr.png")
    print("QR content:", unlock_code)


if __name__ == "__main__":
    create_qr_code()