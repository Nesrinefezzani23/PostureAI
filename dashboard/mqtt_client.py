import json
import threading
from datetime import datetime
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "posture/mesures"

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connecté (code {rc})")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    import django
    django.setup()
    from dashboard.models import Session, RawMeasure, PosturalAnalysis, Alerte
    from django.contrib.auth.models import User
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    try:
        data = json.loads(msg.payload.decode())

        # Récupère ou crée une session active pour le device ESP32
        # On utilise le premier user disponible — adapte selon ton auth
        user = User.objects.first()
        if not user:
            print("[MQTT] Aucun utilisateur trouvé")
            return

        session, created = Session.objects.get_or_create(
            device_id="ESP32_Wokwi",
            fin_session=None,
            defaults={
                'user': user,
                'debut_session': datetime.now(),
                'contexte': 'pc',
                'duree_minutes': 0,
            }
        )

        # 1. Sauvegarder dans RawMeasure
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

        # 2. Sauvegarder dans PosturalAnalysis
        analyse = PosturalAnalysis.objects.create(
            measure=mesure,
            session=session,
            score_posture=data.get('score_posture', 0),
            deviation_dos=data.get('deviation_dos', 0),
            deviation_cou=data.get('deviation_cou', 0),
            symetrie_pression=data.get('symetrie_pression', 100),
            zone_tension=data.get('zone_tension', 'aucune'),
            statut=data.get('statut', 'vert'),
            immobilite_min=data.get('immobilite_min', 0),
            recommandation=data.get('recommandation', ''),
        )

        # 3. Créer une alerte si statut orange ou rouge
        statut = data.get('statut', 'vert')
        if statut in ['orange', 'rouge']:
            Alerte.objects.create(
                user=user,
                analysis=analyse,
                type_alerte='posture' if statut == 'rouge' else 'tension',
                message=data.get('recommandation', ''),
                lue=False,
            )

        # 4. Pousser en temps réel vers le navigateur
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "posture_dashboard",
            {"type": "posture.update", "data": data}
        )

        print(f"[MQTT] OK — score:{data.get('score_posture')} statut:{statut}")

    except Exception as e:
        print(f"[MQTT] Erreur : {e}")
        import traceback
        traceback.print_exc()

def start_mqtt():
    client = mqtt.Client(client_id="django_posture_listener")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_forever()

def start_mqtt_thread():
    t = threading.Thread(target=start_mqtt, daemon=True)
    t.start()
    print("[MQTT] Thread démarré")