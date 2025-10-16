## [0.5.0] - 2025-10-12
### Added
- Translation system : Babel (english + french)
- Pre-commit-config.yaml
### Change
- Update dependencies
- Change Flake8, Black and Bandit for Ruff
- Move benchmarking tool (https://github.com/pyproxytools/pyproxy-benchmark)

## [0.4.6] - 2025-06-12
### Added
- Monitoring : Actions connections table
- Monitoring : Add & Delete blocked domains/URLs
- Monitoring : Searchbar (filerting & Actives connections)
### Change
- Monitoring : change routes

## [0.4.5] - 2025-06-09
### Added
- Monitoring : refresh timer
### Change
- Rework monitoring code

## [0.4.4] - 2025-06-08
### Change
- Repository migration

## [0.4.3] - 2025-06-08
### Added
- Docs: installation from compose
- Custom access & blocked log
### Change
- Default console format

## [0.4.2] - 2025-06-06
### Added
- Custom 403 page for unauthorized IPs
### Change
- Rework code format (server.py, handlers/)

## [0.4.1] - 2025-06-05
### Added
- Custom log format in config.ini
- Add __main__.py to run module
- Colored log

## [0.3.3] - 2025-05-30
### Added
- Change pylint to flake8
- Black scan
- Build and release python package

## [0.3.2] - 2025-05-13
### Added
- Proxy chaining
- List of authorized IPs
## Patch
- Boolean in config ini

## [0.3.1] - 2025-04-26
### Added
- Add slim image
- Benchmark
- Add SAN to generated certificates
- Add docker-compose
- Environment variables usage

## [0.3.0] - 2025-04-26
### Added
- Support header customization
- Monitoring web interface

## [0.2.7] - 2025-04-26
### Added
- Support cancel inspection on site (e.g. bank or medical)
- Support shortcuts
- Hardening docker images
### Patch
- Docker ignore

## [0.2.6] - 2025-03-19
### Added
- Support distant blacklist
### Patch
- Deletion of generated certificates 

## [0.2.5] - 2025-03-18
### Added
- Mode no logging
- Config from file

## [0.2.4] - 2025-03-17
### Added
- Inspection SSL

## [0.2.3] - 2025-03-07
### Added
- HTTPS Filtering domains

## [0.2.2] - 2025-03-07
### Added
- Github Actions Unittest
- Unittest of Filter and Logger modules

## [0.2.1] - 2025-03-07
### Added
- Github Actions Pylint
- Github Actions Docker
- Creation of ProxyServer class

## [0.2.0] - 2025-03-06
### Patch
- Editing page 403.
- Readme update.

## [0.1.0] - 2025-03-06
### Added
- Initialization of the project with the first stable version.
- Basic functionality to proxy and filter streams.