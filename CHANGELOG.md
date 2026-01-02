# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-02

### Added
- **Initial Release**: Core functionality for `gallery-dl` and `megadl` integration.
- **Security**: Implemented dual-app architecture with a camouflage system on port 5492.
- **Archiving**: Added Zstd compression with multi-part chunking support for large files.
- **Storage**: Integrated `rclone` supporting WebDAV, S3, B2, and MEGA.
- **Uploaders**: Native API support for `gofile.io` and custom `openlist` logic.
- **UI**: Responsive Bootstrap 5 interface with real-time job logging and multi-language support (i18n).
- **Automation**: GitHub Actions workflow for automatic Docker image builds and publishing.
- **Deployment**: Added Cloudflare Tunnel integration for easy public access.

### Changed
- Refactored logging system to minimize console noise in production.
- Optimized database schema for better task history tracking.

### Fixed
- Fixed rate-limiting issues with DeviantArt by allowing custom API credentials.
- Resolved temporary file cleanup issues during concurrent jobs.
