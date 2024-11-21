# Changelog

Všechny významné změny v projektu budou dokumentovány v tomto souboru.

Formát je založen na [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
a tento projekt dodržuje [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-03-19

### Přidáno
- Základní funkcionalita pro správu Salesforce oprávnění
- Vytváření permission setů pro objekty a record typy
- Nastavování oprávnění pro čtení a úpravu polí
- Podpora pro standardní i custom objekty
- Konfigurace pomocí YAML souborů
- Detailní logování pomocí elem6-logger
- Unit testy s vysokým pokrytím
- Dokumentace v README.md

### Technické detaily
- Implementace hlavních funkcí v `src/main.py` a `src/salesforce_utils.py`
- Kompletní sada unit testů v `tests/`
- Konfigurace pomocí `.env` souboru
- Závislosti spravované přes `requirements.txt`
