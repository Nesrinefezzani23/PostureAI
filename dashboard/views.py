from django.shortcuts import render
from .models import Session, RawMeasure

def home(request):
    # On récupère quelques stats de la base de données
    total_sessions = Session.objects.count()
    derniere_mesure = RawMeasure.objects.order_by('-timestamp').first()

    context = {
        'total_sessions': total_sessions,
        'derniere_mesure': derniere_mesure,
        'status_ia': "Actif" # Juste pour le test
    }
    return render(request, 'dashboard/index.html', context)