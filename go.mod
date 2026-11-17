module dawn.googlesource.com/dawn

go 1.26

require (
	github.com/fatih/color v1.19.0
	github.com/google/go-cmp v0.7.0
	github.com/mattn/go-colorable v0.1.15
	github.com/mattn/go-isatty v0.0.24
	github.com/mzohreva/gographviz v0.0.0-20180226085351-533f4a37d9c6
	github.com/sergi/go-diff v1.4.0
	github.com/stretchr/testify v1.11.1
	github.com/tidwall/jsonc v0.3.3
	golang.org/x/sync v0.22.0
	golang.org/x/term v0.45.0
)

require (
	github.com/davecgh/go-spew v1.1.2-0.20180830191138-d8f796af33cc // indirect
	github.com/kr/pretty v0.3.1 // indirect
	github.com/mzohreva/GoGraphviz v0.0.0-20180226085351-533f4a37d9c6 // indirect
	github.com/pmezard/go-difflib v1.0.1-0.20181226105442-5d4384ee4fb2 // indirect
	github.com/rogpeppe/go-internal v1.16.0 // indirect
	golang.org/x/sys v0.47.0 // indirect
	gopkg.in/check.v1 v1.0.0-20201130134442-10cb98267c6c // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)

// Some tooling wants dawn.googlesource.com/dawn for the import, but other tooling wants the local path, so provide an
// explicit mapping
replace (
	dawn.googlesource.com/dawn/tools/src/execwrapper => ./tools/src/execwrapper
	dawn.googlesource.com/dawn/tools/src/fileutils => ./tools/src/fileutils
	dawn.googlesource.com/dawn/tools/src/glob => ./tools/src/glob
	dawn.googlesource.com/dawn/tools/src/oswrapper => ./tools/src/oswrapper
	dawn.googlesource.com/dawn/tools/src/progressbar => ./tools/src/progressbar
	dawn.googlesource.com/dawn/tools/src/transform => ./tools/src/transform
	dawn.googlesource.com/dawn/tools/src/utils => ./tools/src/utils
)

exclude github.com/sergi/go-diff v1.2.0
