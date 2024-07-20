# Changelog
All notable changes to this project will be documented in this file

[unreleased]: https://github.com/eugenesvk/xontrib-skim/compare/0.0.5...HEAD
## [Unreleased]
<!-- - ✨ __Added__ -->
  <!-- + new features -->
<!-- - Δ __Changed__ -->
  <!-- + changes in existing functionality -->
<!-- - 🐞 __Fixed__ -->
  <!-- + bug fixes -->
<!-- - 💩 __Deprecated__ -->
  <!-- + soon-to-be removed features -->
<!-- - 🗑️ __Removed__ -->
  <!-- + now removed features -->
<!-- - 🔒 __Security__ -->
  <!-- + vulnerabilities -->

- 🐞 __Fixed__
  + keybind sequences causing an error due to the parser trying to despace a list improperly

[0.0.5]: https://github.com/eugenesvk/xontrib-skim/releases/tag/0.0.5
## [0.0.5]
  - __Changed__
    + make `X_SKIM_KEY_HIST_CWD→` consistent with `X_SKIM_KEY_HIST_Z→` and not prefill skim's query with currently typed command line text

[0.0.4]: https://github.com/eugenesvk/xontrib-skim/releases/tag/0.0.4
## [0.0.4]
  - __Fixed__
    + 🐞 work with changed import paths in xonsh v18
    + 🐞 poetry test
  - __Changed__
    + drop trying to find a binary in a nonexistent cache, which is now very costly, especially with larger `$PATH`s

[0.0.1]: https://github.com/eugenesvk/xontrib-skim/releases/tag/0.0.1
## [0.0.1]
