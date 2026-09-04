.PHONY: all extract build validate site check serve clean

PY ?= python3

all: extract build validate site

extract:
	$(PY) scripts/extract_cslb.py

build: extract
	$(PY) scripts/build_data.py

validate: build
	$(PY) scripts/validate.py

site: validate
	$(PY) scripts/build_site.py

# What CI runs: the gate must pass, then the site must render.
check: site

serve: site
	$(PY) -m http.server 8080 --bind 0.0.0.0 --directory docs

clean:
	rm -f data/_cslb_extract.json data/plumbers.json data/master_list.csv \
	      data/validation_report.json docs/index.html
	rm -rf docs/data
