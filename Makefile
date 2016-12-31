.PHONY: setup
setup:
	setup-blog -d . -n database.db --create-database -u admin --gen-config

.PHONY: certs
certs:
	sudo ./bin/gen-key.sh --self-signed

.PHONY: start
start: create
	docker-compose -f docker-compose.yml up -d cjblog

.PHONY: dev-server
dev-server: create
	docker-compose -f docker-compose.yml up cjblog

.PHONY: create
create: clean
	docker-compose -f docker-compose.yml build cjblog

.PHONY: clean
clean:
	docker-compose -f docker-compose.yml down
