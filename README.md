# The Dialectical Cage and the Glass-Box Governor

> The model proposes. The monitor decides.

A reproducible **reference-monitor prototype**, attack corpus and website accompanying the paper
*The Dialectical Cage and the Glass-Box Governor: A Practice-Based Ethics, Safety Constitution, and
Reference-Monitor Architecture for AI Agents* (Canon, 2026).

- Website: <https://ai.necessaryuniverse.com>
- Paper DOI: [10.5281/zenodo.21278446](https://doi.org/10.5281/zenodo.21278446)
- Contact: canon@necessaryuniverse.com

## What this is, precisely

This repository implements a concrete prototype of **selected execution-security components** described
in the framework, for one closed surface: the *Protected File Mutation Profile v1* (two files, two
effects, three principals), enforced by an in-process monitor. It does **not** claim that the complete
conceptual specification has been implemented.

| Demonstrated by code (locally tested) | Not established |
|---|---|
| Capabilities bound to principal, effect, resource, version, policy hash, expiry | Complete mediation (same-user code can still write the files; this is detected, not prevented) |
| Revocation by id and epoch; single-use nonces; replay blocked | Kernel / OS-level assurance, formal verification |
| State revalidation under one lock (TOCTOU, double-spend races) | Machine-checked policy refinement |
| UNKNOWN safety state fails closed | Delegation with attenuation |
| Deny-by-default policy with an executable admission check | Independent audit, external red team |
| Hash-chained evidence for every decision | Production validation; the paper's philosophical derivations are not machine-checked |

On the committed corpus (`attack-corpus-1`: 65 scenarios in 17 families), 0 of 60 adversarial requests
changed protected state through the full governor, versus 58 of 60 with no monitor and 54 of 60 under a
simple containment-only model. **That is a finite observation, not a proof of zero real-world risk.**
Read [`LIMITATIONS.md`](LIMITATIONS.md) before citing any number.

## Reproduce everything (offline, standard library only)

```bash
git clone https://github.com/canon4d/the-dialectical-cage-and-the-glass-box-governor
cd the-dialectical-cage-and-the-glass-box-governor
python3 scripts/run_release_tests.py      # tests + evaluation + results + manifest + verification
```

Requires Python 3.10+. No packages, no network, no API keys. The command prints a summary and writes
`results/results.json`, `results/results.md` and `results/manifest.json`. Compare the printed
`core_sha256` with the one on <https://ai.necessaryuniverse.com/evidence/>.

## Repository map

| Path | Role | Trusted? |
|---|---|---|
| `governor/` | The reference monitor: capability, policy, state, evidence, executor | **the whole trusted path of v0.1** |
| `profiles/` | Safety Profile, policies, channel inventory | declarative input |
| `evaluation/` | Attack corpus, three arms, ablations, races, bypass probe | untrusted tooling |
| `tests/` | Unit, adversarial, integration tests (one generated test per scenario) | untrusted tooling |
| `scripts/` | Release command, results/manifest builders, verifiers | untrusted tooling |
| `claims/` | Machine-readable claim registry (status, scope, limitations) | documentation |
| `results/` | Generated results, markdown report, manifest | generated |
| `research/` | Paper PDF and LaTeX source, abstract, source map | the paper |
| `web/` | The website (Next.js static export, deployed on Vercel) | presentation only |
| `docs/` | Spec, evidence model, deployment guide, roadmap | documentation |

Start auditing at [`AUDIT.md`](AUDIT.md). Threat model: [`THREAT_MODEL.md`](THREAT_MODEL.md).
Security reports: [`SECURITY.md`](SECURITY.md).

## Common commands

```bash
make test       # unit + adversarial + integration tests
make release    # everything, writes results/
make verify     # re-verify committed results (re-runs the evaluation)
make claims     # regenerate CLAIMS.md from claims/CLAIMS.json
make sync       # copy canonical data into web/
make check      # repository <-> website <-> paper consistency
make web-dev    # run the website locally
```

## Cite

See [`CITATION.cff`](CITATION.cff). BibTeX for the paper is on <https://ai.necessaryuniverse.com/paper/>.

## License

MIT for the code ([`LICENSE`](LICENSE)). The paper PDF and LaTeX source in `research/` are provided for
reading and citation; check the Zenodo record for the licence applied to the paper at publication.
