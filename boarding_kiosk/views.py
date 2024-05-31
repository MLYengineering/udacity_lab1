from django.shortcuts import render
from .utils import get_blob_url

# Create your views here.
def indexView(request):
    blob_url = get_blob_url("django/meat.png")

    # Debugging-Ausgabe
    print(f"Blob URL: {blob_url}")

    context = {
        'blob_url': blob_url
    }

    return render(request, 'boarding_kiosk/index.html', context)