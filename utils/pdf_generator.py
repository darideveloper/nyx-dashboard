import os
import io
from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, legal
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from datetime import datetime, timedelta
import textwrap

current_folder = os.path.dirname (__file__)
parent_folder = os.path.dirname (current_folder)
files_folder = os.path.join (parent_folder, "files")
templates_folder = os.path.join (current_folder, "pdf_utils")
original_pdf = os.path.join (templates_folder, f"template.pdf")
fonts_folder =  os.path.join (templates_folder, "fonts")
montserrat = os.path.join (fonts_folder, f"Montserrat-Regular.ttf")
montserrat_semi_bold = os.path.join (fonts_folder, f"Montserrat-SemiBold.ttf")


def generate_pdf(invoice, date, name, city, state, street, pc, country, phone, email, quantity, base, igi, paypal, total):
    packet = io.BytesIO()
    # Fonts with epecific path
    pdfmetrics.registerFont(TTFont('montserrat', montserrat))
    pdfmetrics.registerFont(TTFont('montserratsbd', montserrat_semi_bold))

    c = canvas.Canvas(packet, legal)

    width, height = legal

    # Invoice details
    c.setFont('montserratsbd', 12)
    c.drawString(516, 808, invoice)
    c.setFont('montserrat', 10)
    c.drawString(455, 790, date)

    # Client details
    c.setFont('montserrat', 10)
    c.drawString(351, 693, name)
    c.drawString(351, 679, city+" , "+state)
    c.drawString(351, 665, street)
    c.drawString(351, 651, pc)
    c.drawString(351, 637, country)
    c.drawString(351, 623, phone)
    c.drawString(351, 609, email)

    # Purchase details
    c.setFont('montserrat', 10)
    c.drawString(200, 466, quantity)
    c.drawString(224, 466, base+"USD")
    c.drawString(301, 466, igi+"USD")
    c.drawString(410, 466, paypal+"USD")
    c.drawString(526, 466, total+"USD")

    # Purchase details
    c.setFont('montserrat', 10)
    c.drawString(511, 318, base+"USD")
    c.drawString(511, 284, igi+"USD")
    c.drawString(511, 243, paypal+"USD")
    c.drawString(511, 203, total+"USD")

    c.showPage()
    c.save()

    packet.seek(0)

    new_pdf = PdfReader(packet)
    
    existing_pdf = PdfReader(open(original_pdf, "rb"))
    output = PdfWriter()
    
    #Creación página
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)

    new_pdf = os.path.join (files_folder, f"file.pdf")
    output_stream = open(new_pdf, "wb")
    output.write(output_stream)
    output_stream.close()
    print("Documentos generados correctamente")
    
    return new_pdf

#generatePDF("00100", "19 de Mayo de 2025", "Aaron Preziosi Jr", "Billerica", "Massachusetts", "19 Greenville Street", "01821", "United States", "970-988-5711", "wisptech970@gmail.com", "1", "290.24", "14.4", "15.36", "320")
    
