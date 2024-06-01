from django.shortcuts import render, redirect
from .utils import get_blob_url, list_blobs_in_subfolder, add_to_session_dict, get_id_card_details, get_boardingpass_details, get_manifest, process_person_documents

# Create your views here.
def indexView(request):
    blob_url = get_blob_url("django/wallpaper.png")

    # Debugging-Ausgabe
    print(f"Blob URL: {blob_url}")

    context = {
        'blob_url': blob_url
    }

    return render(request, 'boarding_kiosk/index.html', context)


def boardingpass(request):
    blob_url = get_blob_url("django/wallpaper.png")
    list_boardingpasses = list_blobs_in_subfolder('boardingcards/')

    if request.method == 'POST':
        selected_blob = request.POST.get('selected_blob')
        add_to_session_dict(request, 'boardingpass', selected_blob)
        print(request.session.get('session_dict', {}))
        
        return redirect('idcard')  # Ersetze 'next_view_name' mit dem tatsächlichen View-Namen
  

    context = {
        'blob_url': blob_url,
        'list_boardingpasses' : list_boardingpasses
    }

    return render(request, 'boarding_kiosk/boardingpass.html', context)


def idcard(request):
    blob_url = get_blob_url("django/wallpaper.png")
    list_idcards = list_blobs_in_subfolder('digital_IDs/')

    if request.method == 'POST':
        selected_blob = request.POST.get('selected_blob')
        add_to_session_dict(request, 'id', selected_blob)
        print(request.session.get('session_dict', {}))
        
        return redirect('verification')  # Ersetze 'next_view_name' mit dem tatsächlichen View-Namen
  

    context = {
        'blob_url': blob_url,
        'list_idcards' : list_idcards
    }

    return render(request, 'boarding_kiosk/idcard.html', context)

def verification(request):
    blob_url = get_blob_url("django/wallpaper.png")
    request_dict = request.session.get('session_dict', {})
    request_dict.get('id', None)
    id = request_dict.get('id', None)
    boardingpass = request_dict.get('boardingpass', None)
    #boardingpass = get_boardingpass_details (request_dict.get('boardingpass', None))
    flight_manifest = get_manifest()
    message = process_person_documents(id, boardingpass, flight_manifest)

    context = {
        'blob_url': blob_url,
        'message' : message
    }

    return render(request, 'boarding_kiosk/verification.html', context)