# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-03-19

### Added
- New function `create_edit_permission_set` for creating edit permission sets
- Support for restricted_fields in configuration
- Enhanced logging using elem6-logger
- Pre-commit hooks for code checking
- Extended configuration for Account object

### Changed
- Restructured project for better modularity
- Improved error and exception handling
- Updated documentation in README.md
- Optimized tests with better coverage

### Fixed
- Proper error handling when creating permission sets
- Validation of access_level in set_field_permissions

## [1.0.0] - 2024-03-19

### Added
- Basic functionality for Salesforce permission management
- Creation of permission sets for objects and record types
- Setting read and edit permissions for fields
- Support for standard and custom objects
- Configuration using YAML files
- Detailed logging
- Unit tests
- Documentation in README.md

### Technical Details
- Implementation of main functions in `src/main.py` and `src/salesforce_utils.py`
- Complete set of unit tests in `tests/`
- Configuration using `.env` file
- Dependencies managed through `requirements.txt`
