from django.contrib import admin
# On importe tous les modèles
from .models import (
    Profile, 
    Session, 
    RawMeasure, 
    PosturalAnalysis, 
    Alerte, 
    Rapport
)

# On les enregistre
admin.site.register(Profile)
admin.site.register(Session)
admin.site.register(RawMeasure)
admin.site.register(PosturalAnalysis)
admin.site.register(Alerte)
admin.site.register(Rapport)