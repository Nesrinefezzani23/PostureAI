from django.shortcuts import render
from .models import Session, RawMeasure, PosturalAnalysis
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import RawMeasureSerializer
from .ai_engine import analyze_posture_data

def home(request):
    """
    Affiche le dashboard avec les dernières données et l'utilisateur de la session.
    """
    # 1. Statistiques globales
    total_sessions = Session.objects.count()
    
    # 2. Dernière mesure brute reçue
    derniere_mesure = RawMeasure.objects.order_by('-timestamp').first()

    # 3. Analyse IA la plus récente
    derniere_analyse = PosturalAnalysis.objects.order_by('-timestamp_analyse').first()

    # 4. Récupération du nom de l'utilisateur
    nom_utilisateur = "Inspecteur" # Valeur par défaut
    
    if derniere_mesure and derniere_mesure.session:
        # On récupère le nom associé à la session (seyf dans ton cas)
        nom_utilisateur = derniere_mesure.session.user

    context = {
        'total_sessions': total_sessions,
        'derniere_mesure': derniere_mesure,
        'derniere_analyse': derniere_analyse,
        'nom_utilisateur': nom_utilisateur,
        'status_ia': "Actif"
    }
    return render(request, 'dashboard/index.html', context)

@api_view(['POST'])
def receive_data(request):
    """
    API pour l'ESP32.
    """
    serializer = RawMeasureSerializer(data=request.data)
    if serializer.is_valid():
        measure = serializer.save() 
        analysis_results = analyze_posture_data(measure)
        
        PosturalAnalysis.objects.create(
            measure=measure,
            session=measure.session,
            score_posture=analysis_results['score'],
            deviation_dos=analysis_results['deviation'],
            deviation_cou=0.0, 
            symetrie_pression=0.0, 
            zone_tension="Dos",
            statut=analysis_results['statut'],
            immobilite_min=0,
            recommandation=analysis_results['recommandation']
        )
        return Response({"status": "success"}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)