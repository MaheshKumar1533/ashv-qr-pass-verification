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
# def add_members(request):
#     if request.method == "POST" and request.FILES.get("file"):
#         excel_file = request.FILES["file"]
#         df = pd.read_excel(excel_file)
        
#         for _, row in df.iterrows():
#             GatePass.objects.create(
#                 pass_number=row["pass_number"],
#                 holder_name=row["holder_name"],
#                 valid_until=row["valid_until"],
#                 members=row["members"]
#             )
        
#         return JsonResponse({"status": "success", "message": "Members added successfully"})
#     return JsonResponse({"status": "error", "message": "Invalid request"})
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import qrcode
import zipfile
from django.core.files.storage import default_storage
from django.http import HttpResponse

def generate_passes(request):
    visitors = GatePass.objects.all()
    template_path = 'static/gatepass.jpeg'
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        if default_storage.exists(template_path):
            with default_storage.open(template_path, 'rb') as f:
                template_img = Image.open(f).convert("RGB")
        else:
            template_img = Image.new("RGB", (1240, 1754), "white")  # Default A4 size
        
        for visitor in visitors:
            img = template_img.copy()
            draw = ImageDraw.Draw(img)
            
            # Generate QR Code
            qr = qrcode.make(f"{visitor.pass_number}")
            qr = qr.resize((170, 170)).convert("L")
            
            # Paste QR Code onto the image
            qr_x, qr_y = 1030, 338
            img.paste(qr, (qr_x, qr_y))
            
            # Load font (adjust path and size as needed)
            font_large = ImageFont.truetype(font="Roboto-Black.ttf", size=34)
            font_small = ImageFont.truetype(font="Roboto-Black.ttf", size=24)
            
            # Choose font size based on name length
            font = font_small if len(visitor.holder_name) > 15 else font_large
            
            # Add Visitor Info
            if font == font_large:
                draw.text((390, 338), visitor.holder_name.upper(), fill="white", font=font) 
            else:
                draw.text((390, 343), visitor.holder_name.upper(), fill="white", font=font) 
            draw.text((510, 392), visitor.pass_number, fill="white", font=font_large)
            draw.text((500, 445), visitor.event.name, fill="white", font=font_large)
            
            # Save as image in memory
            img_buffer = BytesIO()
            img.save(img_buffer, format="JPEG")
            img_buffer.seek(0)
            
            img_filename = f"{visitor.holder_name}_{visitor.event.name}.jpeg"
            zip_file.writestr(img_filename, img_buffer.getvalue())
            
            img_buffer.close()
    
    zip_buffer.seek(0)
    return FileResponse(zip_buffer, as_attachment=True, filename="visitor_passes.zip")

def generate_pass(request, pass_id):
    visitor = GatePass.objects.get(pass_number=pass_id)
    template_path = 'static/gatepass.jpeg'
    
    if default_storage.exists(template_path):
        with default_storage.open(template_path, 'rb') as f:
            template_img = Image.open(f)
            width, height = template_img.size
    else:
        width, height = A4  # Default to A4 if template is missing

    if default_storage.exists(template_path):
        with default_storage.open(template_path, 'rb') as f:
            template_img = Image.open(f).convert("RGB")
    else:
        template_img = Image.new("RGB", (1240, 1754), "white")  # Default A4 size

    img = template_img.copy()
    draw = ImageDraw.Draw(img)
    
    # Generate QR Code
    qr = qrcode.make(f"{visitor.pass_number}")
    qr = qr.resize((170, 170)).convert("L")
    
    # Paste QR Code onto the image
    qr_x, qr_y = 1030, 338
    img.paste(qr, (qr_x, qr_y))
    
    # Load font (adjust path and size as needed)
    font_large = ImageFont.truetype(font="Roboto-Black.ttf", size=34)
    font_small = ImageFont.truetype(font="Roboto-Black.ttf", size=24)
    
    # Choose font size based on name length
    font = font_small if len(visitor.holder_name) > 15 else font_large
    
    # Add Visitor Info
    if font == font_large:
        draw.text((390, 338), visitor.holder_name.upper(), fill="white", font=font) 
    else:
        draw.text((390, 343), visitor.holder_name.upper(), fill="white", font=font) 
    draw.text((510, 392), visitor.pass_number, fill="white", font=font_large)
    draw.text((500, 445), visitor.event.name, fill="white", font=font_large)
    
    # Save as image in memory
    img_buffer = BytesIO()
    img.save(img_buffer, format="JPEG")
    img_buffer.seek(0)
    
    img_filename = f"{visitor.holder_name}_{visitor.event.name}.jpeg"
    return FileResponse(img_buffer, as_attachment=True, filename=f"visitor_pass_{pass_id}.jpeg")

def add_members(request):
    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES["file"]
        df = pd.read_csv(csv_file)
        
        required_columns = ['Person_name', 'Members', 'event_name', 'Category']
        for column in required_columns:
            if column not in df.columns:
                return JsonResponse({"status": "error", "message": f"Missing required column: {column}"})

        for _, row in df.iterrows():
            event_name = row["event_name"]
            event_model = get_object_or_404(event, name=event_name)
            pass_no = randint(100000, 999999)
            while GatePass.objects.filter(pass_number=pass_no).exists():
                pass_no = randint(100000, 999999)

            GatePass.objects.create(
                pass_number=pass_no,
                holder_name=row["Person_name"],
                event_id=event_model.id,  # Correctly use event.id instead of row["event_id"]
            )
        
        return JsonResponse({"status": "success", "message": "Members added successfully"})
    return render(request, 'add_members.html')