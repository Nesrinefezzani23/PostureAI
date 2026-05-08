import uuid
from django.db import models
from django.contrib.auth.models import User

# 1. Profil utilisateur (extension de l'utilisateur Django)
class Profile(models.Model):
    ACTIVITE_CHOICES = [
        ('sedentaire', 'Sédentaire'),
        ('actif', 'Actif'),
        ('sportif', 'Sportif')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    id_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    taille = models.FloatField(null=True, blank=True)
    poids_kg = models.FloatField(null=True, blank=True)
    activite = models.CharField(max_length=100, choices=ACTIVITE_CHOICES, default='sedentaire')
    pathologies = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profil de {self.user.username}"

# 2. Session
class Session(models.Model):
    id_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    debut_session = models.DateTimeField()
    fin_session = models.DateTimeField(null=True, blank=True)
    duree_minutes = models.IntegerField(default=0)
    device_id = models.CharField(max_length=100)
    contexte = models.CharField(max_length=50) # assis / debout / pc

    def __str__(self):
        return f"Session {self.id_uuid} - {self.user.username}"
    
# 3. Mesures Brutes
class RawMeasure(models.Model):
    id_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='measures')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Accéléromètre & Gyroscope
    acc_x = models.FloatField()
    acc_y = models.FloatField()
    acc_z = models.FloatField()
    gyro_x = models.FloatField()
    gyro_y = models.FloatField()
    gyro_z = models.FloatField()
    
    # Inclinaison & Flexion
    pitch = models.FloatField()
    roll = models.FloatField()
    flex_lombaire = models.FloatField()
    flex_thoracique = models.FloatField()
    flex_cervical = models.FloatField()
    
    # Capteurs de pression (Ischions et Cuisses)
    pression_ischion_g = models.FloatField()
    pression_ischion_d = models.FloatField()
    pression_cuisse_g = models.FloatField()
    pression_cuisse_d = models.FloatField()

    def __str__(self):
        return f"Mesure {self.timestamp} - Session {self.session.id_uuid}"
    
# 4. Analyses Posturales (Calculé par l'IA)
class PosturalAnalysis(models.Model):
    id_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    measure = models.OneToOneField(RawMeasure, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    score_posture = models.IntegerField() # 0-100
    deviation_dos = models.FloatField()
    deviation_cou = models.FloatField()
    symetrie_pression = models.FloatField()
    zone_tension = models.CharField(max_length=100)
    statut = models.CharField(max_length=20, choices=[('vert', 'Vert'), ('orange', 'Orange'), ('rouge', 'Rouge')])
    immobilite_min = models.IntegerField()
    recommandation = models.TextField()
    timestamp_analyse = models.DateTimeField(auto_now_add=True)

# 5. Alertes
class Alerte(models.Model):
    id_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    analysis = models.ForeignKey(PosturalAnalysis, on_delete=models.CASCADE)
    type_alerte = models.CharField(max_length=50) # posture / pause / tension
    message = models.TextField()
    declenchee_at = models.DateTimeField(auto_now_add=True)
    lue = models.BooleanField(default=False)

# 6. Rapports (Export PDF)
class Rapport(models.Model):
    id_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    periode_debut = models.DateField()
    periode_fin = models.DateField()
    score_moyen = models.FloatField()
    progression_pct = models.FloatField()
    export_pdf_url = models.URLField(max_length=500, null=True, blank=True)
    genere_at = models.DateTimeField(auto_now_add=True)