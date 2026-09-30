# Avisa Lá

Lembretes por contexto (GPS simulado, SQLite, banner AdMob de teste).

## Rodar no navegador
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    flet run --web main.py

## Gerar o APK
    flet build apk --android-meta-data com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-3940256099942544~3347511713

IDs de teste do AdMob. Troque pelos reais antes de publicar.
