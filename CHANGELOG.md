# Changelog

All notable changes to the Gemma Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Live Timer Display** in Workflow Builder
  - Real-time elapsed time display during workflow execution
  - Updates every 100ms for smooth visual feedback
  - Positioned in toolbar after Enable/Disable button
  - Displays timing in completion popups
  - Supports multiple time formats: seconds, minutes:seconds, hours:minutes
  - Gray-blue styling with RIDGE relief for visual distinction

### Changed
- Updated README.md with timer feature documentation

## [0.1.0-feature-hooks] - 2026-02-09

### Added
- Advanced Hooks & Sideloading system for SDR integration
- Pre-hooks: Run scripts before app starts
- Post-hooks: Auto-collect logs after completion
- Persistent hooks: Background monitors throughout test
- Sideloading: Step-specific cleanup/verification scripts
- Centralized "Automation Logs" output system
- Chronological organization of all production results
- AI annotations showing decision-making process

### Changed
- Renamed output directories to `automation_logs` and `automation_screenshots`
- Improved Workflow Builder UI with hooks toggle button

### Fixed
- Case sensitivity issues with bulk string input
- Application focus handling for hidden windows

## [0.1.0-initial] - 2026-01-15

### Added
- Initial release of Gemma Framework
- Controller-Agent architecture
- Workflow Builder with point & click interface
- AI-driven UI element detection (OmniParser/Qwen)
- Multi-SUT Command Center
- YAML-based workflow definitions
- Network-based SUT communication
- Screenshot capture and analysis
- Windows SendInput API integration

---

## Contribution Guide

When adding entries to this changelog:
1. Add unreleased changes under `[Unreleased]`
2. Use categories: Added, Changed, Deprecated, Removed, Fixed, Security
3. Keep descriptions concise and user-focused
4. Link to relevant PRs or issues when applicable
