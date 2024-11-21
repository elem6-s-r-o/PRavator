# PRavator

PRavator is a Python tool for managing Salesforce object permissions. It enables automatic creation of permission sets and setting permissions for object fields with support for different access levels.

## Features

- Creation of basic and edit permission sets
- Setting read and edit permissions for fields
- Support for standard and custom objects
- Configuration using YAML files
- Detailed logging using elem6-logger
- CLI interface for flexible usage

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/PRavator.git
cd PRavator
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # For Linux/Mac
# or
.\venv\Scripts\activate  # For Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Configuration

1. Create a `.env` file with your Salesforce credentials:
```env
SF_USERNAME=your_salesforce_username@example.com
SF_PASSWORD=your_salesforce_password
SF_SECURITY_TOKEN=your_salesforce_security_token
SF_DOMAIN=test.salesforce.com  # or login.salesforce.com for production
```

2. Create a configuration YAML file for each object in the `config/` directory. For example `config/Account.yaml`:
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

restricted_fields:
  - OwnerId
  - SystemModstamp
```

## Usage

PRavator offers several execution options:

1. Process all objects:
```bash
python src/main.py --all
```

2. Process all custom objects:
```bash
python src/main.py --custom-all
```

3. Process specific objects:
```bash
python src/main.py --objects Account Contact Custom__c
```

## Testing

Run tests:
```bash
python -m pytest tests/
```

Run tests with coverage:
```bash
python -m pytest tests/ --cov=src
```

## Project Structure

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

## Detailed Functions

### Salesforce Utils

- `connect_to_salesforce`: Connect to Salesforce instance
- `create_permission_set`: Create permission set for object and record type
- `set_field_permissions`: Set permissions for object fields
- `create_edit_permission_set`: Create edit permission set

### Main

- Command line argument processing
- Loading configuration from YAML files
- Getting list of objects from Salesforce
- Setting permissions according to configuration

## Logging

The project uses elem6-logger for detailed operation logging. Logs include:
- Salesforce connection information
- Permission set creation
- Field permission settings
- Errors and exceptions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/NewFeature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` file for more information.
