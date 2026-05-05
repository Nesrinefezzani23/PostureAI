def analyze_posture_data(raw_data):
    """
    Prend un objet RawMeasure et retourne un dictionnaire 
    contenant l'analyse IA.
    """
    # 1. Calcul du score global (exemple de logique)
    # Plus le pitch et les flexions s'éloignent de 0, plus le score baisse
    base_score = 100
    penalite_pitch = abs(raw_data.pitch) * 1.5
    penalite_flexion = (raw_data.flex_lombaire + raw_data.flex_thoracique) / 20
    
    score = max(0, int(base_score - penalite_pitch - penalite_flexion))

    # 2. Détermination du statut
    if score > 80:
        statut = 'vert'
        recommandation = "Excellente posture. Continuez ainsi !"
    elif score > 50:
        statut = 'orange'
        recommandation = "Attention, vous commencez à vous affaisser. Redressez votre buste."
    else:
        statut = 'rouge'
        recommandation = "Posture critique ! Levez-vous pour vous étirer ou changez de position immédiatement."

    # 3. Analyse de symétrie (Ischions)
    diff_pression = abs(raw_data.pression_ischion_g - raw_data.pression_ischion_d)
    if diff_pression > 0.3:
        recommandation += " Note : Vous vous appuyez trop sur un seul côté."

    return {
        'score': score,
        'statut': statut,
        'recommandation': recommandation,
        'deviation': raw_data.pitch
    }