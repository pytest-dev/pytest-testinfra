all: doc

DOC_BUILD:=./doc/build/html
LOCAL_BIND:=127.0.0.1

doc: ## generate documentation
	$(MAKE) -C doc html

serve: ## run a local server to serve the generated doc
	python -m http.server --bind $(LOCAL_BIND) --directory $(DOC_BUILD)

.PHONY: all doc
