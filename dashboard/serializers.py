from rest_framework import serializers
from .models import RawMeasure

class RawMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawMeasure
        # On liste les champs que l'ESP32 va envoyer
        fields = [
            'session', 'acc_x', 'acc_y', 'acc_z', 
            'gyro_x', 'gyro_y', 'gyro_z', 'pitch', 'roll', 
            'flex_lombaire', 'flex_thoracique', 'flex_cervical',
            'pression_ischion_g', 'pression_ischion_d', 
            'pression_cuisse_g', 'pression_cuisse_d'
        ]