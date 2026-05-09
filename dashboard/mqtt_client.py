import json
import threading
import time
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "posture/mesures"

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connecté (code {rc})")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        # Import Django ici, pas au niveau module
        import django
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

        from dashboard.models import Session, RawMeasure, PosturalAnalysis, Alerte
        from django.contrib.auth.models import User
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        user = User.objects.first()
        if not user:
            print("[MQTT] Aucun utilisateur trouvé")
            return

        # Session active ou création
        session, _ = Session.objects.get_or_create(
            device_id="ESP32_Wokwi",
            fin_session=None,
            defaults={
                'user': user,
                'debut_session': __import__('django.utils.timezone', fromlist=['now']).now(),
                'contexte': 'pc',
                'duree_minutes': 0,
            }
        )

        # Sauvegarde RawMeasure
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

        # Sauvegarde PosturalAnalysis
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

        # Alerte si orange ou rouge
        statut = data.get('statut', 'vert')
        if statut in ['orange', 'rouge']:
            Alerte.objects.create(
                user=user,
                analysis=analyse,
                type_alerte='posture' if statut == 'rouge' else 'tension',
                message=data.get('recommandation', ''),
                lue=False,
            )

        # ── Push WebSocket vers le navigateur ──
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "posture_dashboard",
            {
                "type": "posture.update",
                "data": data
            }
        )

        print(f"[MQTT] OK — score:{data.get('score_posture')} statut:{statut} → WS envoyé")

    except Exception as e:
        print(f"[MQTT] Erreur : {e}")
        import traceback
        traceback.print_exc()

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
            print(f"[MQTT] Déconnecté : {e} — retry dans 5s")
            time.sleep(5)

def start_mqtt_thread():
    # Attendre que Django soit complètement prêt
    time.sleep(2)
    t = threading.Thread(target=start_mqtt, daemon=True)
    t.start()
    print("[MQTT] Thread démarré")