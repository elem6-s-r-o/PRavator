# PRavator

PRavator je nástroj pro správu oprávnění Salesforce objektů. Umožňuje automatické vytváření permission setů a nastavování oprávnění pro pole objektů.

## Instalace

1. Naklonujte repozitář:
```bash
git clone https://github.com/your-username/PRavator.git
cd PRavator
```

2. Vytvořte a aktivujte virtuální prostředí:
```bash
python -m venv venv
source venv/bin/activate  # Pro Linux/Mac
# nebo
.\venv\Scripts\activate  # Pro Windows
```

3. Nainstalujte závislosti:
```bash
pip install -r requirements.txt
```

4. Vytvořte soubor `.env` s vašimi Salesforce přihlašovacími údaji:
```env
SF_USERNAME=your_salesforce_username@example.com
SF_PASSWORD=your_salesforce_password
SF_SECURITY_TOKEN=your_salesforce_security_token
SF_DOMAIN=test.salesforce.com  # nebo login.salesforce.com pro produkci
```

## Konfigurace

Pro každý objekt vytvořte konfigurační YAML soubor v adresáři `config/`. Například `config/Account.yaml`:

```yaml
record_types:
  - Customer
  - Partner

fields:
  read:
    - Name
    - Description
    - Industry
  edit:
    - Status
    - Rating
```

## Použití

PRavator nabízí několik možností spuštění:

1. Zpracování všech objektů:
```bash
python src/main.py --all
```

2. Zpracování všech custom objektů:
```bash
python src/main.py --custom-all
```

3. Zpracování konkrétních objektů:
```bash
python src/main.py --objects Account Contact Custom__c
```

## Testování

Spuštění testů:
```bash
python -m pytest tests/
```

Spuštění testů s pokrytím:
```bash
python -m pytest tests/ --cov=src
```

## Struktura projektu

```
PRavator/
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── salesforce_utils.py
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_salesforce_utils.py
├── config/
│   └── Account.yaml
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── CHANGELOG.md
```

## Funkce

- Vytváření permission setů pro objekty a jejich record typy
- Nastavování oprávnění pro čtení a úpravu polí
- Podpora pro standardní i custom objekty
- Flexibilní konfigurace pomocí YAML souborů
- Detailní logování operací

## Přispívání

1. Fork repozitáře
2. Vytvoření feature branche (`git checkout -b feature/AmazingFeature`)
3. Commit změn (`git commit -m 'Add some AmazingFeature'`)
4. Push do branche (`git push origin feature/AmazingFeature`)
5. Otevření Pull Requestu

## Licence

Distribuováno pod MIT licencí. Viz `LICENSE` soubor pro více informací.
