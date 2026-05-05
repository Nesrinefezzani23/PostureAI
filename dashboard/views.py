from django.shortcuts import render
from .models import Session, RawMeasure, PosturalAnalysis
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import RawMeasureSerializer
from .ai_engine import analyze_posture_data
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg

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

def historique(request):
    """
    Vue pour l'historique compact avec graphique hebdomadaire.
    """
    aujourdhui = timezone.now().date()
    # Création propre de la liste des 7 derniers jours (du plus vieux au plus récent)
    derniers_7_jours = [aujourdhui - timedelta(days=i) for i in range(6, -1, -1)]
    
    labels_jours = []
    scores_jours = []
    
    # Boucle corrigée pour itérer sur la liste des jours
    for jour in derniers_7_jours:
        # Formatage de l'étiquette (ex: "05 mai")
        labels_jours.append(jour.strftime('%d %b'))
        
        # Calcul de la moyenne pour ce jour précis
        stat_du_jour = PosturalAnalysis.objects.filter(
            timestamp_analyse__date=jour
        ).aggregate(moyenne_score=Avg('score_posture'))
        
        score_moyen = stat_du_jour['moyenne_score']
        # On ajoute le score arrondi ou 0 si pas de données pour tracer la ligne
        if score_moyen is not None:
            scores_jours.append(round(score_moyen, 1))
        else:
            scores_jours.append(0) 

    # Récupération compacte des dernières analyses pour le tableau
    dernieres_analyses = PosturalAnalysis.objects.order_by('-timestamp_analyse')[:5]

    context = {
        'labels_jours': labels_jours,
        'scores_jours': scores_jours,
        'dernieres_analyses': dernieres_analyses,
    }
    return render(request, 'dashboard/historique.html', context)