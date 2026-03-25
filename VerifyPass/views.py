from django.shortcuts import render, redirect
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
import json
from django.contrib.auth.decorators import login_required
from django.db.models import Min
from django.views.decorators.http import require_GET
from django.utils import timezone

@login_required
def home(request):
    if request.method == "POST":
        pass_num = request.POST.get("pass_number")
        holder_name = request.POST.get("holder_name")
        rollno = request.POST.get("roll_number")
        phone_num = request.POST.get("phone")
        id_num = request.POST.get("id_proof")
        evented = request.POST.get("event")

        gated_form = GatePass.objects.get(pass_number=pass_num)

        created = gated_form.holder_name

        if created != "":
            checkedin, checkin_created = checkin.objects.get_or_create(holder=gated_form)
            if checkin_created:
                return render(request, 'home.html', {'form': GatePassForm(), 'message': "✅Checked in"})
            else:
                return render(request, 'home.html', {'form': GatePassForm(), 'message': "❌Already Checked in"})
         
        # Retrieve or create the event object
        event_obj = event.objects.get(id=evented)

        # Update the gate pass object with new values
        gated_form.holder_name = holder_name
        gated_form.phone = phone_num
        gated_form.roll_number = rollno
        gated_form.id_proof = id_num
        gated_form.event = event_obj
        gated_form.save()

        checked = checkin.objects.create(holder=gated_form)
        checked.save()

        # Retrieve or create the check-in record
        return render(request, 'home.html', {'form': GatePassForm(), 'message': "✅Gate pass added successfully and checked in"})


    events = event.objects.all()
    
    return render(request, 'home.html', {'form': GatePassForm(), 'events': events})

from django.core.serializers import serialize

@login_required
def check_pass(request):
    if request.method == "GET":
        pass_number = request.GET.get("pass_number", "").strip()
        GatePas = GatePass.objects.filter(pass_number=pass_number)
        print(GatePas)
        if GatePas.exists():
            checkedin = checkin.objects.filter(holder=GatePas[0])
            if checkedin.exists():
                return JsonResponse({"valid": False, "message": "Already Checked in"})
            else:
                gatepass_data = serialize('json', GatePas)  # If GatePas is a QuerySet
                return JsonResponse({"valid": True, "gatepass": gatepass_data})
        return JsonResponse({"valid": False, "message": "Invalid QR Detected"})
    return JsonResponse({"valid": False})


@require_GET
def verify_pass_api(request, pass_number=None):
    query_pass_number = (pass_number or request.GET.get("pass_number", "")).strip()

    if not query_pass_number:
        return JsonResponse(
            {
                "verified": False,
                "message": "pass_number is required",
            },
            status=400,
        )

    gate_pass = GatePass.objects.select_related("event").filter(pass_number=query_pass_number).first()

    if gate_pass is None:
        return JsonResponse(
            {
                "verified": False,
                "message": "Pass not found",
                "pass_number": query_pass_number,
            },
            status=404,
        )

    checkins = checkin.objects.filter(holder=gate_pass).order_by("checkin_time")
    latest_checkin = checkins.last()

    is_valid_date = gate_pass.valid_until >= timezone.localdate()

    return JsonResponse(
        {
            "verified": True,
            "message": "Pass verified successfully",
            "pass": {
                "pass_number": gate_pass.pass_number,
                "holder_name": gate_pass.holder_name,
                "roll_number": gate_pass.roll_number,
                "college": gate_pass.college,
                "phone": gate_pass.phone,
                "id_proof": gate_pass.id_proof,
                "event": {
                    "id": gate_pass.event.id,
                    "name": gate_pass.event.name,
                    "category": gate_pass.event.category,
                },
                "valid_until": gate_pass.valid_until,
                "referred_by": gate_pass.referred_by,
            },
            "verification": {
                "is_valid_date": is_valid_date,
                "is_checked_in": checkins.exists(),
                "checkin_count": checkins.count(),
                "latest_checkin_time": latest_checkin.checkin_time if latest_checkin else None,
            },
        }
    )

@login_required
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

@login_required
def generate_passes_category(request, category):
    visitors = GatePass.objects.filter(event__category=category)
    subquery = GatePass.objects.filter(event__category=category) \
                           .values('holder_name') \
                           .annotate(min_id=Min('id')) \
                           .values('min_id')

    visitors = GatePass.objects.filter(id__in=subquery)
    template_path = 'static/GatePass Template.jpg'
    zip_buffer = BytesIO()
    zip_buffer.seek(0)
    zip_buffer.truncate()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        template_img = get_template_image(template_path)
        
        for visitor in visitors:
            img = create_pass_image(visitor, template_img)
            
            # Save as image in memory
            img_buffer = BytesIO()
            img.save(img_buffer, format="JPEG")
            img_buffer.seek(0)
            
            img_filename = f"{visitor.holder_name}_{visitor.event.name}_{visitor.pass_number}.jpeg"
            zip_file.writestr(img_filename, img_buffer.getvalue())
            
            img_buffer.close()
    
    zip_buffer.seek(0)
    return FileResponse(zip_buffer, as_attachment=True, filename="visitor_passes.zip")

def get_template_image(template_path):
    if default_storage.exists(template_path):
        with default_storage.open(template_path, 'rb') as f:
            return Image.open(f).convert("RGB")
    return Image.new("RGB", (1240, 1754), "white")  # Default A4 size

def create_pass_image(visitor, template_img):
    img = template_img.copy()
    draw = ImageDraw.Draw(img)
    
    # Generate QR Code
    qr = qrcode.make(f"{visitor.pass_number}")
    qr = qr.resize((200, 200)).convert("L")
    
    # Paste QR Code onto the image
    qr_x, qr_y = 160, 1380
    img.paste(qr, (qr_x, qr_y))
    
    # Load font (adjust path and size as needed)
    font_large = ImageFont.truetype(font="Roboto-Black.ttf", size=44)
    font_small = ImageFont.truetype(font="Roboto-Black.ttf", size=34)
    
    # Choose font size based on name length
    font = font_small if len(visitor.holder_name) > 35 else font_large

    event_name = visitor.event.name[:35] + "..." if len(visitor.event.name) > 35 else visitor.event.name
    college = ""

    if visitor.college and len(visitor.college) > 35:
        college = visitor.college[:35] + "..."
    else:
        college = visitor.college
    
    # Add Visitor Info
    if font == font_large:
        draw.text((350, 1010), visitor.holder_name.title(), fill="black", font=font) 
    else:
        draw.text((350, 1015), visitor.holder_name.title(), fill="black", font=font) 
    draw.text((350, 1100), event_name, fill="black", font=font)
    draw.text((350, 1190), college or "", fill="black", font=font)
    draw.text((350, 1280), visitor.pass_number, fill="black", font=font)
    
    return img

@login_required
def generate_passes(request):
    visitors = GatePass.objects.exclude(holder_name="")
    subquery = GatePass.objects.exclude(holder_name="") \
                           .values('holder_name') \
                           .annotate(min_id=Min('id')) \
                           .values('min_id')

    visitors = GatePass.objects.filter(id__in=subquery)
    template_path = 'static/GatePass Template.jpg'
    zip_buffer = BytesIO()
    zip_buffer.seek(0)
    zip_buffer.truncate()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        template_img = get_template_image(template_path)
        
        for visitor in visitors:
            img = create_pass_image(visitor, template_img)
            
            # Save as image in memory
            img_buffer = BytesIO()
            img.save(img_buffer, format="JPEG")
            img_buffer.seek(0)
            
            img_filename = f"{visitor.holder_name}_{visitor.event.name}_{visitor.pass_number}.jpeg"
            zip_file.writestr(img_filename, img_buffer.getvalue())
            
            img_buffer.close()
    
    zip_buffer.seek(0)
    return FileResponse(zip_buffer, as_attachment=True, filename="visitor_passes.zip")

@login_required
def generate_pass(request, pass_id):
    visitor = GatePass.objects.get(pass_number=pass_id)
    template_path = 'static/GatePass Template.jpg'
    
    template_img = get_template_image(template_path)
    img = create_pass_image(visitor, template_img)
    
    # Save as image in memory
    img_buffer = BytesIO()
    img.save(img_buffer, format="JPEG")
    img_buffer.seek(0)
    
    img_filename = f"{visitor.holder_name}_{visitor.event.name}_{visitor.pass_number}.jpeg"
    return FileResponse(img_buffer, as_attachment=True, filename=img_filename)

@login_required
def add_members(request):
    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES["file"]
        df = pd.read_csv(csv_file)
        
        required_columns = ['Name', 'Event', 'Category', 'College Name']
        for column in required_columns:
            if column not in df.columns:
                return JsonResponse({"status": "error", "message": f"Missing required column: {column}"})
        for _, row in df.iterrows():
            event_name = row["Event"]
            event_model, _ = event.objects.get_or_create(name=event_name, category=row["Category"])
            pass_no = randint(100000, 999999)
            while GatePass.objects.filter(pass_number=pass_no).exists():
                pass_no = randint(100000, 999999)

            GatePass.objects.create(
                pass_number=pass_no,
                holder_name=row["Name"],
                event_id=event_model.id,  # Correctly use event.id instead of row["event_id"]
                college=row["College Name"]
            )
        
        return JsonResponse({"status": "success", "message": "Members added successfully"})
    return render(request, 'add_members.html')

@login_required
def generate_empty_passes(request, count):
    c = 0
    for _ in range(int(count)):
        pass_no = randint(100000, 999999)
        while GatePass.objects.filter(pass_number=pass_no).exists():
            pass_no = randint(100000, 999999)

        GatePass.objects.create(
            pass_number=pass_no,
            holder_name="",
            event_id=1,
        )
        c+=1
    
    return JsonResponse({"status": "success", "message": f"{c} Empty passes generated successfully"})

@login_required
def empty_passes(request):
    visitors = GatePass.objects.filter(event__category="external")
    zip_buffer = BytesIO()
    zip_buffer.seek(0)
    zip_buffer.truncate()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        template_path = 'static/GatePass Template.jpg'
        template_img = get_template_image(template_path)
        
        for visitor in visitors:
            img = template_img.copy()
            draw = ImageDraw.Draw(img)
            
            # Generate QR Code
            qr = qrcode.make(f"{visitor.pass_number}")
            qr = qr.resize((200, 200)).convert("L")
            
            # Paste QR Code onto the image
            qr_x, qr_y = 160, 1380
            img.paste(qr, (qr_x, qr_y))

            font_large = ImageFont.truetype(font="Roboto-Black.ttf", size=44)
            draw.text((350, 1280), visitor.pass_number, fill="black", font=font_large)
            
            # Save as image in memory
            img_buffer = BytesIO()
            img.save(img_buffer, format="JPEG")
            img_buffer.seek(0)
            
            img_filename = f"{visitor.event.name}_{visitor.pass_number}.jpeg"
            zip_file.writestr(img_filename, img_buffer.getvalue())
            
            img_buffer.close()
    
    zip_buffer.seek(0)
    return FileResponse(zip_buffer, as_attachment=True, filename="visitor_passes.zip")

@login_required
def show_checkins(request):
    checkin_members = checkin.objects.all()
    checkin_data = checkin_members.select_related('holder')
    print(checkin_data)
    return render(request, 'checkins.html', {'checkins': checkin_data})

@login_required
def show_externals(request):
    external_members = GatePass.objects.filter(event__id=11).exclude(holder_name="")
    return render(request, 'externals.html', {'externals': external_members})


from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout

def login_view(request):
    if request.method == "POST":
        user = request.POST.get("username")
        password = request.POST.get("password")
        user_obj = authenticate(request, username=user, password=password)
        if user_obj is not None:
            login(request, user_obj)
            return redirect('home')
    return render(request, 'login.html', {'error': 'Invalid username or password'})

def logout_view(request):
    logout(request)
    return redirect('login_view')

# python manage.py runserver_plus --cert-file cert.crt --key-file cert.key 0.0.0.0:8000