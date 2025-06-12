import os
import io
from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import legal
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


current_folder = os.path.dirname(__file__)
parent_folder = os.path.dirname(current_folder)
files_folder = os.path.join(parent_folder, "files")

# Create files folder in case it doesn't exist
os.makedirs(files_folder, exist_ok=True)

templates_folder = os.path.join(current_folder, "pdf_utils")
original_pdf = os.path.join(templates_folder, "template.pdf")
fonts_folder = os.path.join(templates_folder, "fonts")
montserrat = os.path.join(fonts_folder, "Montserrat-Regular.ttf")
montserrat_semi_bold = os.path.join(fonts_folder, "Montserrat-SemiBold.ttf")


def generate_invoice(
    invoice: str,
    date: str,
    name: str,
    city: str,
    state: str,
    street: str,
    pc: str,
    country: str,
    phone: str,
    email: str,
    quantity: str,
    base: str,
    igi: str,
    paypal: str,
    total: str,
) -> str:
    """Generate invoice PDF from data

    Args:
        invoice (str): _description_
        date (str): _description_
        name (str): _description_
        city (str): _description_
        state (str): _description_
        street (str): _description_
        pc (str): _description_
        country (str): _description_
        phone (str): _description_
        email (str): _description_
        quantity (str): _description_
        base (str): _description_
        igi (str): _description_
        paypal (str): _description_
        total (str): _description_

    Returns:
        str: Generated path file
    """

    packet = io.BytesIO()
    # Fonts with epecific path
    pdfmetrics.registerFont(TTFont("montserrat", montserrat))
    pdfmetrics.registerFont(TTFont("montserratsbd", montserrat_semi_bold))

    c = canvas.Canvas(packet, legal)

    width, height = legal

    # Invoice details
    c.setFont("montserratsbd", 12)
    c.drawString(516, 808, invoice)
    c.setFont("montserrat", 10)
    c.drawRightString(552, 790, f"Fecha: {date}")

    # Client details
    c.setFont("montserrat", 10)
    c.drawString(351, 693, name)
    c.drawString(351, 679, city + " , " + state)
    c.drawString(351, 665, street)
    c.drawString(351, 651, pc)
    c.drawString(351, 637, country)
    c.drawString(351, 623, phone)
    c.drawString(351, 609, email)

    # Purchase details
    c.setFont("montserrat", 10)
    c.drawString(200, 466, quantity)
    c.drawString(224, 466, base + "USD")
    c.drawString(301, 466, igi + "USD")
    c.drawString(410, 466, paypal + "USD")
    c.drawString(526, 466, total + "USD")

    # Purchase details
    c.setFont("montserrat", 10)
    c.drawRightString(551, 318, base + "USD")
    c.drawRightString(551, 284, igi + "USD")
    c.drawRightString(551, 243, paypal + "USD")
    c.drawRightString(551, 203, total + "USD")

    c.showPage()
    c.save()

    packet.seek(0)

    new_pdf = PdfReader(packet)

    existing_pdf = PdfReader(open(original_pdf, "rb"))
    output = PdfWriter()

    # Page creation
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)

    new_pdf = os.path.join(files_folder, f"{invoice}.pdf")
    output_stream = open(new_pdf, "wb")
    output.write(output_stream)
    output_stream.close()
    print(f"Invoice {invoice} generated correctly")

    return new_pdf


if __name__ == "__main__":
    generate_invoice(
        "00100",
        "19 de Septiembre de 2025",
        "Aaron Preziosi Jr",
        "Billerica",
        "Massachusetts",
        "19 Greenville Street",
        "01821",
        "United States",
        "970-988-5711",
        "wisptech970@gmail.com",
        "1",
        "290.24",
        "14.4",
        "15.36",
        "320",
    )
