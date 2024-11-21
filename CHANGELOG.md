# Changelog

Všechny významné změny v projektu budou dokumentovány v tomto souboru.

Formát je založen na [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
a tento projekt dodržuje [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-03-19

### Přidáno
- Nová funkce `create_edit_permission_set` pro vytváření editačních permission setů
- Podpora pro restricted_fields v konfiguraci
- Vylepšené logování pomocí elem6-logger
- Pre-commit hooks pro kontrolu kódu
- Rozšířená konfigurace pro Account objekt

### Změněno
- Přepracovaná struktura projektu pro lepší modularitu
- Vylepšené zpracování chyb a výjimek
- Aktualizovaná dokumentace v README.md
- Optimalizované testy s lepším pokrytím

### Opraveno
- Správné zpracování chyb při vytváření permission setů
- Validace access_level v set_field_permissions

## [1.0.0] - 2024-03-19

### Přidáno
- Základní funkcionalita pro správu Salesforce oprávnění
- Vytváření permission setů pro objekty a record typy
- Nastavování oprávnění pro čtení a úpravu polí
- Podpora pro standardní i custom objekty
- Konfigurace pomocí YAML souborů
- Detailní logování
- Unit testy
- Dokumentace v README.md

### Technické detaily
- Implementace hlavních funkcí v `src/main.py` a `src/salesforce_utils.py`
- Kompletní sada unit testů v `tests/`
- Konfigurace pomocí `.env` souboru
- Závislosti spravované přes `requirements.txt`
