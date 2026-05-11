# PostureAI 🧘‍♂️

## À propos
**PostureAI** est une solution intelligente dédiée à la santé posturale. Grâce à une technologie de suivi en temps réel et une intelligence artificielle intégrée, PostureAI aide les utilisateurs à corriger leur posture au quotidien, prévenant ainsi les douleurs chroniques et favorisant un meilleur bien-être au travail.

---

## 🚀 Fonctionnalités clés
*   **Analyse Posturale en temps réel** : Détection instantanée des déviations de posture via capteurs connectés.
*   **Dashboard Intuitif** : Visualisation claire des statistiques de posture (temps passé en bonne/mauvaise position).
*   **Alertes Intelligentes** : Notifications haptiques et sonores immédiates en cas de mauvaise posture prolongée.
*   **Recommandations IA** : Conseils personnalisés générés par l'IA pour améliorer votre ergonomie.
*   **Gestion Utilisateur** : Suivi historique personnalisé.

---

## 🛠 Architecture Technique
PostureAI est une plateforme complète composée de deux piliers majeurs :

1.  **Backend (Django)** : Gère la logique métier, l'authentification et le traitement des données des capteurs via WebSockets.
2.  **Frontend (Flutter)** : Application mobile multiplateforme offrant une expérience utilisateur fluide et un tableau de bord moderne.

---

## 📥 Installation

### Prérequis
*   [Python 3.x](https://www.python.org/)
*   [Flutter SDK](https://flutter.dev/)

### Backend (Dashboard/API)
```bash
# Dans le dossier racine
python -m venv venv
# Activer l'environnement virtuel
pip install -r requirements.txt
python manage.py runserver
```

### Application Mobile (Flutter)
```bash
cd mobile_app
flutter pub get
flutter run
```

---

## 🎨 Design & Expérience Utilisateur
Le dashboard est conçu avec une approche **Modern UI**, utilisant des gradients fluides, des graphiques dynamiques (`fl_chart`) et des composants hautement interactifs pour rendre le suivi de santé aussi engageant que possible.

---

## 🤝 Contribution
Le projet est ouvert à toute contribution visant à améliorer les algorithmes de détection de posture ou à enrichir l'expérience mobile.

---

*Développé avec passion pour votre santé.*
