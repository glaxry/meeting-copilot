# Day1 Version Record: v0.1.1

## Change summary

This patch version switches the project workflow from a repo-local Miniconda installation to the machine's existing Anaconda installation at `D:\anaconda`.

## What changed

- helper scripts now default to Anaconda instead of `.miniconda3`
- Conda environment creation uses `D:\anaconda\Scripts\conda.exe`
- environment automation now forces `--no-plugins --solver classic` to match this machine's Conda behavior
- helper scripts resolve env Python from both `D:\anaconda\envs` and `C:\Users\11212\.conda\envs`
- test and API scripts now work with the actual resolved Anaconda env path
- documentation was updated to reflect the Anaconda-based workflow
- the obsolete Miniconda installer script was removed from the project workflow

## Why this change matters

- it matches your local setup
- it removes duplicate Conda distributions for the same project
- it keeps Python execution inside an Anaconda-managed environment as required
- it handles this machine's actual Conda env placement instead of assuming a fixed env directory

## Verified results

- Anaconda environment created successfully
- active env path resolved to `C:\Users\11212\.conda\envs\meeting-copilot-day1`
- `pytest` passed: `3 passed, 1 warning`
- native extension rebuilt successfully against the Anaconda env Python
- `/health` still reports `cpp_backend_available: true`
