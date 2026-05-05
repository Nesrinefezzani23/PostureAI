from django.shortcuts import render
from .models import Session, RawMeasure
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import RawMeasureSerializer

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

@api_view(['POST'])
def receive_data(request):
    """
    Point d'entrée pour que l'ESP32 envoie ses mesures
    """
    serializer = RawMeasureSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save() # Enregistre directement dans la base de données !
        return Response({"status": "success", "message": "Données reçues"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)