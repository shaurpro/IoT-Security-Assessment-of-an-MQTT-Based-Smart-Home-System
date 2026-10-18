# Convenience targets. Run `make help` for the list.
# These wrap the same commands documented in the README so the workflow is
# reproducible with a single verb.

PY ?= python3

.PHONY: help install certs passwords baseline hardened sensors \
        attack-eavesdrop attack-spoof acl-test down clean

help:
	@echo "Targets:"
	@echo "  install          pip install dependencies"
	@echo "  certs            generate lab TLS certificates"
	@echo "  passwords        build the hardened broker password file"
	@echo "  baseline         start the insecure broker (docker, port 1883)"
	@echo "  hardened         start the hardened broker (docker, port 8883)"
	@echo "  sensors          run temperature + motion sensors (MODE=baseline|hardened)"
	@echo "  attack-eavesdrop run the anonymous-eavesdrop PoC"
	@echo "  attack-spoof     run the unauthorized-publish PoC"
	@echo "  acl-test         run the access-control verification matrix"
	@echo "  down             stop all broker containers"
	@echo "  clean            down + remove generated certs/passwords"

install:
	$(PY) -m pip install -r requirements.txt

certs:
	bash config/mosquitto/certs/generate_certs.sh

passwords:
	bash scripts/make_passwords.sh

baseline:
	docker compose --profile baseline up -d

hardened:
	docker compose --profile hardened up -d

sensors:
	bash scripts/run_sensors.sh

attack-eavesdrop:
	$(PY) src/attacks/eavesdrop.py --duration 10

attack-spoof:
	$(PY) src/attacks/spoof_publish.py --value 99.9

acl-test:
	$(PY) src/attacks/acl_test.py

down:
	docker compose --profile baseline --profile hardened down 2>/dev/null || true

clean: down
	rm -f config/mosquitto/certs/*.crt config/mosquitto/certs/*.key \
	      config/mosquitto/certs/*.csr config/mosquitto/certs/*.srl \
	      config/mosquitto/hardened/passwordfile
	@echo "cleaned generated certs and password file"
