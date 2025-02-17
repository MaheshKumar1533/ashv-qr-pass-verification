from django.shortcuts import render
from django.http import JsonResponse
from .models import GatePass,checkin, event
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.core.files.storage import default_storage
from reportlab.lib.utils import ImageReader
import qrcode
from PIL import Image
from .forms import CheckinForm, GatePassForm
from random import randint

def home(request):
    if request.method == "POST":
        Gatedform = GatePassForm(request.POST)
        if form.is_valid():
            form.save()
            checked = checkin.objects.create(holder=gate_pass, checkin_members=gate_pass.event__members)
            checked.save()

            return JsonResponse({"status": "success", "message": "Checkin added successfully"})
        return JsonResponse({"status": "error", "message": "Invalid form data"})
    return render(request, 'home.html', {'form': GatePassForm()})

def check_pass(request):
    if request.method == "GET":
        pass_number = request.GET.get("pass_number", "").strip()
        GatePas = GatePass.objects.filter(pass_number=pass_number)
        if GatePas.exists():
            return JsonResponse({"valid": True, "gatepass": GatePas.first()})
        return JsonResponse({"valid": False})
    return JsonResponse({"valid": False, "passno": ""})

def add_checkin(request):
    if request.method == "POST":
        pass_number = request.POST.get("pass_number", "").strip()
        checkin_members = request.POST.get("checkin_members", "").strip()
        GatePas = GatePass.objects.filter(pass_number=pass_number).first()
        if GatePas:
            check = checkin.objects.create(holder=GatePas, checkin_members=checkin_members)
            check.save()
            return JsonResponse({"status": "success", "message": "Checkin added successfully"})
        return JsonResponse({"status": "error", "message": "Invalid pass number"})
    return JsonResponse({"status": "error", "message": "Invalid request"})

###################### Ignore Lines Below ######################
def add_members(request):
    if request.method == "POST" and request.FILES.get("file"):
        excel_file = request.FILES["file"]
        df = pd.read_excel(excel_file)
        
        for _, row in df.iterrows():
            GatePass.objects.create(
                pass_number=row["pass_number"],
                holder_name=row["holder_name"],
                valid_until=row["valid_until"],
                members=row["members"]
            )
        
        return JsonResponse({"status": "success", "message": "Members added successfully"})
    return JsonResponse({"status": "error", "message": "Invalid request"})
def generate_passes(request):
    visitors = GatePass.objects.all()
    template_path = 'static/gatepass.jpeg'
    
    if default_storage.exists(template_path):
        with default_storage.open(template_path, 'rb') as f:
            template_img = Image.open(f)
            width, height = template_img.size
    else:
        width, height = A4  # Default to A4 if template is missing
    
    for visitor in visitors:
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=(width, height))
        
        if default_storage.exists(template_path):
            template = ImageReader(template_path)
            p.drawImage(template, 0, 0, width, height)
        
        # Generate QR Code
        qr = qrcode.make(f"s{visitor.id}")
        qr = qr.resize((100, 100))
        qr = qr.convert("L")
        qr_data = qr.getdata()
        
        # Draw QR Code directly on PDF
        qr_size = 100
        x_start, y_start = width - 150, height - 200
        p.setFillGray(0)
        pixel_size = qr_size / qr.width
        
        for row in range(qr.height):
            for col in range(qr.width):
                if qr_data[row * qr.width + col] < 128:
                    x = x_start + (col * pixel_size)
                    y = y_start + (qr_size - row * pixel_size)
                    p.rect(x, y, pixel_size, pixel_size, fill=1)
        
        # Add Visitor Info with White Font Color
        p.setFillColorRGB(1, 1, 1)  # Set font color to white
        p.setFont("Helvetica-Bold", 14)
        p.drawString(100, height - 150, f"{visitor.holder_name}")
        
        p.showPage()
        p.save()
        buffer.seek(0)
        
        # Save PDF without returning it
        pdf_path = f"visitor_passes/visitor_{visitor.id}.pdf"
        with default_storage.open(pdf_path, 'wb') as pdf_file:
            pdf_file.write(buffer.getvalue())
        
        buffer.close()

def generate_pass(request, pass_id):
    visitor = GatePass.objects.get(pass_number=pass_id)
    template_path = 'static/gatepass.jpeg'
    
    if default_storage.exists(template_path):
        with default_storage.open(template_path, 'rb') as f:
            template_img = Image.open(f)
            width, height = template_img.size
    else:
        width, height = A4  # Default to A4 if template is missing

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=(width, height))
    
    if default_storage.exists(template_path):
        template = ImageReader(template_path)
        p.drawImage(template, 0, 0, width, height)
    
    # Generate QR Code
    qr = qrcode.make(f"s{visitor.id}")
    qr = qr.resize((180, 180))
    qr = qr.convert("L")
    qr_data = qr.getdata()
    
    # Draw QR Code directly on PDF
    qr_size = 180
    x_start, y_start = width - 258, height - 513
    p.setFillGray(0)
    pixel_size = qr_size / qr.width
    
    for row in range(qr.height):
        for col in range(qr.width):
            if qr_data[row * qr.width + col] < 128:
                x = x_start + (col * pixel_size)
                y = y_start + (qr_size - row * pixel_size)
                p.rect(x, y, pixel_size, pixel_size, fill=1)
    
    # Add Visitor Info with White Font Color
    p.setFillColorRGB(1, 1, 1)  # Set font color to white
    p.setFont("Helvetica-Bold", 34)
    p.drawString(390, height - 370, f"{visitor.holder_name}")
    p.drawString(505, height - 424, f"{visitor.pass_number}")
    p.drawString(500, height - 478, f"{visitor.event.name}")
    
    p.showPage()
    p.save()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=f"visitor_pass_{pass_id}.pdf")

def add_members(request):
    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES["file"]
        df = pd.read_csv(csv_file)
        
        required_columns = ['pass_number', 'holder_name', 'valid_until', 'name', 'email', 'phone', 'id_proof', 'event_id']
        for column in required_columns:
            if column not in df.columns:
                return JsonResponse({"status": "error", "message": f"Missing required column: {column}"})

        for _, row in df.iterrows():
            event_id = get_object_or_404(event, pk=row["event_id"])
            GatePass.objects.create(
                pass_number=row["pass_number"],
                holder_name=row["holder_name"],
                valid_until=row["valid_until"],
                name=row["name"],
                email=row["email"],
                phone=row["phone"],
                id_proof=row["id_proof"],
                event_id=row["event_id"]
            )
        
        return JsonResponse({"status": "success", "message": "Members added successfully"})
    return render(request, 'add_members.html')