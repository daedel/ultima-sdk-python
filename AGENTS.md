## Project
ultima-sdk-python is a production Python package for working with Ultima Online data, assets, and SDK-style tooling.
Prefer reusable library code over one-off scripts.
Assume this repo is used by developers who need stable APIs, clear typing, and deterministic behavior.

## Priorities
- Keep changes small and surgical unless a larger refactor is explicitly requested.
- Preserve public API compatibility unless the task explicitly allows breaking changes.
- Prefer explicit, readable code over clever abstractions.
- Do not add placeholders, fake implementations, or TODO-driven partial work.
- When adding features, update docs, examples, and tests in the same change when applicable.

## Code style
- Target modern Python already used by the repo; match existing style before introducing new patterns.
- Use type hints on public functions, methods, and dataclasses.
- Prefer pure functions and small utilities where practical.
- Raise clear exceptions with useful messages; fail fast on invalid inputs.
- Avoid hidden side effects, global state, and magic path assumptions.

## Package design
- Treat this repo as a library first, CLI/scripts second.
- Keep parsing, transformation, and I/O concerns separated.
- Public-facing modules should stay stable and well documented.
- If a new dependency is not clearly necessary, ask first.
- Prefer standard library modules unless a third-party package materially improves correctness or maintainability.

## Files and safety
- Do not rename or move public modules without checking for import impact.
- Do not delete tests, fixtures, or sample data unless the task requires it.
- Ask before making destructive changes, adding heavyweight dependencies, or changing package structure.
- Never commit secrets, tokens, machine-specific paths, or generated junk.

## Testing
- Run the smallest relevant test scope first, then broaden only as needed.
- Add or update tests for behavior changes and bug fixes.
- Prefer deterministic tests; avoid network dependency unless the repo already uses recorded/live integration patterns.
- If parsing binary or asset data, include at least one fixture-based validation path.

## Documentation
- Update README, docstrings, and usage examples when public behavior changes.
- Keep examples copy-pasteable and consistent with the real API.
- Document assumptions around Ultima Online formats, version differences, and edge cases near the code.

## Agent workflow
- Read nearby modules and tests before editing.
- Match existing naming, folder structure, and test patterns.
- When unsure, choose the option that keeps the SDK predictable and easy to extend.
- Surface tradeoffs briefly in your final notes if a change affects compatibility, performance, or format support.
- If you need to make a judgment call, choose the option that minimizes risk and preserves future flexibility.

## Communication
- If you encounter a task that is unclear, seems to require a large refactor, or appears to conflict with the priorities above, ask for clarification before proceeding.
- If you make a judgment call that deviates from the instructions, document your reasoning and any tradeoffs in the final notes.
