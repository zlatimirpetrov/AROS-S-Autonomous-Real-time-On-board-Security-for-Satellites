# Contributing to AROS-S

Thank you for your interest in AROS-S. Contributions, bug reports, and questions are
all welcome.

## Reporting bugs or asking for help

Please open an issue on the
[issue tracker](https://github.com/zlatimirpetrov/AROS-S-Autonomous-Real-time-On-board-Security-for-Satellites/issues).
For a bug, include:

- what you ran (command and environment: OS, Python version),
- what you expected to happen,
- what actually happened (full error output if any).

For questions or support, an issue is also the best place — that way the answer helps
the next person too.

## Requesting features

Open an issue describing the use case and what you would like AROS-S to do. Feature
ideas that keep the detector lightweight and suitable for onboard / resource-constrained
deployment are especially welcome.

## Proposing changes (pull requests)

1. Fork the repository and create a branch for your change.
2. Install the dependencies: `pip install -r requirements.txt`.
3. Make your change, keeping the code style consistent with the surrounding code.
4. Run the tests and make sure they pass:
   ```bash
   python -m tests.final_audit
   python -m tests.test_model_equivalence
   ```
5. If you change behaviour, update the README and add or adjust a test.
6. Open a pull request describing what you changed and why.

## Code of conduct

Please be respectful and constructive in all interactions. Discussion should stay
focused on the technical work and on helping each other.

## License

By contributing, you agree that your contributions will be licensed under the same
[MIT License](LICENSE) that covers this project.
