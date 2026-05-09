import json
import threading
import time
import numpy as np
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "posture/mesures"

_model  = None
_scaler = None

def get_model():
    global _model, _scaler
    if _model is None:
        import os, joblib
        base    = os.path.dirname(os.path.abspath(__file__))
        _scaler = joblib.load(os.path.join(base, 'ml/posture_scaler.pkl'))
        _model  = joblib.load(os.path.join(base, 'ml/posture_model.pkl'))
        print("[IA] Modèle RandomForest chargé")
    return _model, _scaler

def predict_posture(data):
    try:
        model, scaler = get_model()

        flex_cerv = data.get('flex_cervical', 0)

        # Si flex_cervical = 0 → ADC2 bloqué par Wi-Fi → fallback ESP32
        if flex_cerv == 0:
            statut = data.get('statut', 'vert')
            score  = data.get('score_posture', 0)
            print(f"[IA] flex_cervical=0 → fallback ESP32 : {statut} score:{score}")
            return statut, score, 0

        features = np.array([[
            data['pitch'], data['roll'],
            data['acc_x'], data['acc_y'], data['acc_z'],
            data['gyro_x'], data['gyro_y'], data['gyro_z'],
            data['flex_lombaire'], data['flex_thoracique'], data['flex_cervical'],
            data['pression_ischion_g'], data['pression_ischion_d'],
            data['pression_cuisse_g'], data['pression_cuisse_d'],
        ]])
        features_scaled = scaler.transform(features)
        proba   = model.predict_proba(features_scaled)[0]
        classe  = int(np.argmax(proba))
        confiance = int(proba[classe] * 100)
        statuts = ['vert', 'orange', 'rouge']
        scores  = [100, 60, 20]
        score   = max(0, scores[classe] - (100 - confiance) // 2)
        print(f"[IA] Prédiction : {statuts[classe]} (confiance {confiance}%) score:{score}")
        return statuts[classe], score, confiance

    except Exception as e:
        print(f"[IA] Erreur : {e}")
        return data.get('statut', 'vert'), data.get('score_posture', 0), 0

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connecté (code {rc})")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

        from dashboard.models import Session, RawMeasure, PosturalAnalysis, Alerte
        from django.contrib.auth.models import User
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from django.utils import timezone

        user = User.objects.first()
        if not user:
            return

        session, _ = Session.objects.get_or_create(
            device_id="ESP32_Wokwi",
            fin_session=None,
            defaults={
                'user': user,
                'debut_session': timezone.now(),
                'contexte': 'pc',
                'duree_minutes': 0,
            }
        )

        mesure = RawMeasure.objects.create(
            session=session,
            acc_x=data.get('acc_x', 0),
            acc_y=data.get('acc_y', 0),
            acc_z=data.get('acc_z', 0),
            gyro_x=data.get('gyro_x', 0),
            gyro_y=data.get('gyro_y', 0),
            gyro_z=data.get('gyro_z', 0),
            pitch=data.get('pitch', 0),
            roll=data.get('roll', 0),
            flex_lombaire=data.get('flex_lombaire', 0),
            flex_thoracique=data.get('flex_thoracique', 0),
            flex_cervical=data.get('flex_cervical', 0),
            pression_ischion_g=data.get('pression_ischion_g', 0),
            pression_ischion_d=data.get('pression_ischion_d', 0),
            pression_cuisse_g=data.get('pression_cuisse_g', 0),
            pression_cuisse_d=data.get('pression_cuisse_d', 0),
        )

        # ── Prédiction IA ──
        statut_ia, score_ia, confiance = predict_posture(data)
        data['statut']        = statut_ia
        data['score_posture'] = score_ia

        analyse = PosturalAnalysis.objects.create(
            measure=mesure,
            session=session,
            score_posture=score_ia,
            deviation_dos=data.get('deviation_dos', 0),
            deviation_cou=data.get('deviation_cou', 0),
            symetrie_pression=data.get('symetrie_pression', 100),
            zone_tension=data.get('zone_tension', 'aucune'),
            statut=statut_ia,
            immobilite_min=data.get('immobilite_min', 0),
            recommandation=data.get('recommandation', ''),
        )

        if statut_ia in ['orange', 'rouge']:
            Alerte.objects.create(
                user=user,
                analysis=analyse,
                type_alerte='posture' if statut_ia == 'rouge' else 'tension',
                message=data.get('recommandation', ''),
                lue=False,
            )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "posture_dashboard",
            {"type": "posture.update", "data": data}
        )

        print(f"[MQTT] OK → WS envoyé")

    except Exception as e:
        print(f"[MQTT] Erreur : {e}")
        import traceback; traceback.print_exc()

def start_mqtt():
    while True:
        try:
            print("[MQTT] Connexion au broker...")
            client = mqtt.Client(client_id="django_posture_listener_01")
            client.on_connect = on_connect
            client.on_message = on_message
            client.connect(BROKER, PORT, 60)
            client.loop_forever()
        except Exception as e:
            print(f"[MQTT] Déconnecté : {e} — retry 5s")
            time.sleep(5)

def start_mqtt_thread():
    time.sleep(2)
    t = threading.Thread(target=start_mqtt, daemon=True)
    t.start()
    print("[MQTT] Thread démarré")