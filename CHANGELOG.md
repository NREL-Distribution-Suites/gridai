# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - yyyy-mm-dd

### Added 
- Added project-optional doc and lint dependencies in toml file
- Added a module named analyze_dataset to give statistics around the input data
- Added cli command to generate stats for the dataset

### Fixed
- Fixed linting issues across the repo.
- Applied black formatter to all python files
- Updated to get largest connected component without any loops
- Updated to only read Master.dss files from deepest directory

### Removed
- Removed default lint, format and coverage from pyproject.toml file populated by hatch
- Removed unnecessary classifiers from pyproject.toml file

### Changed
