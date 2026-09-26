# CHANGELOG

All notable changes to the Integrated Systems Oncology Framework are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] – 2026-09-26

### Changed
- Synchronized repository metadata to version 1.0.2.
- Updated README, architecture documentation, mathematical specification, and parameter reference to match the current implementation.
- Clarified that the Tumor Evolution Engine uses a discrete stochastic birth–death–mutation process; it does not apply an explicit replicator-dynamics selection operator.
- Clarified that the master orchestrator runs engines sequentially and does not perform live step-by-step state transfer between engines.
- Updated the active repository structure so the superseded manuscript and its 16 legacy figures are preserved under `archive/` while the active manuscript remains under `manuscript/`.
- Added a repository/metadata release note distinguishing the v1.0.2 repository state from the v1.0.1 manuscript/software archival version.

### Fixed
- Removed stale parameter names and outdated mathematical descriptions from the active documentation.
- Corrected the README installation example and repository folder description.
- Removed the obsolete external `references.bib` dependency from the active project documentation (the manuscript bibliography is embedded in `main.tex`).

### Release notes
- **No functional simulation-engine code changes were made in v1.0.2.**
- The Zenodo v1.0.2 version-specific DOI is 10.5281/zenodo.22980897.

---

## [1.0.1] – 2026-08-03

Versioned archival release documented by the current manuscript. The version-specific Zenodo record is `10.5281/zenodo.21773219`; the concept DOI is `10.5281/zenodo.21773218`.

---

## [1.0.0] – Historical entry

The original public software release. The historical details below are retained for release-history purposes; the current implementation and equations are documented in the v1.0.2 files.

### Added
- Four simulation engines covering tumor evolution, metabolism, epigenetics, and systems-level synergy.
- Engine-level and project-wide validation suites.
- Master orchestration script.
- Core documentation and software metadata.

### Validation
- Engine and project-wide validation suites were established for the public release.
