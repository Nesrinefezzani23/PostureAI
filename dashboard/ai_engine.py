def analyze_posture_data(raw_data):
    """
    Analyse la posture avec les nouvelles règles métier.
    """
    # Conversion forcée en float des données
    flex_cervical = float(raw_data.flex_cervical)
    p_ischion_g = float(raw_data.pression_ischion_g)
    p_ischion_d = float(raw_data.pression_ischion_d)
    pitch = float(raw_data.pitch)

    score = 100
    zone_tension = "Dos"
    recommandation = "Posture optimale."

    # 1. Pénalité Cervicale
    if flex_cervical > 1200:
        score -= 30
        zone_tension = "Cervicale"
        recommandation = "Attention à votre nuque, redressez-vous."

    # 2. Pénalité Assise (Asymétrie)
    diff_pression = abs(p_ischion_g - p_ischion_d)
    if diff_pression > 0.4:
        score -= 20
        zone_tension = "Hanches (Asymétrie)"
        recommandation = "Répartissez mieux votre poids sur l'assise."

    # 3. Pénalité Thoracique
    if pitch > 30:
        score -= 30
        zone_tension = "Thoracique"
        recommandation = "Buste trop incliné, redressez votre dos."

    # Score plancher
    score = max(0, score)

    # 4. Statut couleur
    if score >= 80:
        statut = 'vert'
    elif score >= 50:
        statut = 'orange'
    else:
        statut = 'rouge'

    return {
        'score': score,
        'statut': statut,
        'recommandation': recommandation,
        'deviation': pitch,
        'deviation_cou': flex_cervical,
        'symetrie_pression': diff_pression,
        'zone_tension': zone_tension
    }