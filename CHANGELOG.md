# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Complete project restructuring following simplified Plan B approach
- New directory structure: scripts/{core,tools,selectors,lib}
- Data organization: data/{raw,processed,results,baseline}
- Documentation navigation with docs/README.md
- Standard configuration files (.gitignore, CONTRIBUTING.md)
- Baseline metrics for regression testing

### Changed
- Updated all imports to use new lib.* structure
- Reorganized 11 Python scripts into functional subdirectories
- Moved 9 historical documents to docs/history/
- Updated config.py with new data paths

### Refactored
- Split monolithic scripts directory into modular structure
- Separated concerns: core workflows, tools, selectors, shared libraries

---

## [1.0.0] - 2024-12-15

### Added
- Initial complete implementation
- A-stage clustering (HDBSCAN)
- B-stage within-direction clustering
- HTML viewer generation
- Cluster statistics and validation tools
- Interactive direction selector
- Comprehensive documentation

### Features
- Semantic clustering using sentence-transformers
- Dynamic parameter calculation based on data volume
- Example phrases extraction for each cluster
- Automatic HTML report generation
- GUI-based folder selection for data import
