.PHONY: all test test-py test-ts build report verify clean

all: build test report

build:
	cd typescript && npm install --silent && npx tsc -p tsconfig.json

test: test-py test-ts

test-py:
	cd python && python3 -m unittest discover tests

test-ts: build
	node typescript/dist/test.js

report:
	cd python && python3 -m abjad.cli report --out ../docs

# cross-check: the Python and TypeScript engines must agree exactly
verify: build
	@python3 python/dump.py > /tmp/abjad-py.json
	@node typescript/dist/dump.js > /tmp/abjad-ts.json
	@python3 -c "import json,sys; \
a=json.load(open('/tmp/abjad-py.json',encoding='utf-8')); \
b=json.load(open('/tmp/abjad-ts.json',encoding='utf-8')); \
print('engines agree' if a==b else 'ENGINES DISAGREE'); sys.exit(0 if a==b else 1)"

clean:
	rm -rf typescript/dist typescript/node_modules python/abjad/__pycache__ python/tests/__pycache__
