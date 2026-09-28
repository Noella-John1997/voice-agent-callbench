# `.github/workflows/`

`ci.yml` runs on every push and pull request:

1. Installs the package with dev dependencies.
2. Runs `pytest`.
3. Runs the full scenario suite with `--fail-under 0.5` - the build fails if the demo agent's pass rate
   drops below 50%. Point `--target` at your own agent's staging URL to gate real releases.
