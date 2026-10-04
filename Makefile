.PHONY: test release verify claims sync check web-dev web-build

test:      ## unit + adversarial + integration tests
	python3 -m unittest discover -s tests -t .

release:   ## tests + evaluation + results + manifest + verification
	python3 scripts/run_release_tests.py

verify:
	python3 scripts/verify_results.py

claims:
	python3 scripts/generate_claims_snapshot.py

sync:      ## copy canonical artifacts into web/
	python3 scripts/sync_web_data.py

check:     ## public consistency (repo <-> website <-> paper)
	python3 scripts/verify_public_consistency.py

web-dev:
	cd web && npm install && npm run dev

web-build:
	cd web && npm install && npm run build
