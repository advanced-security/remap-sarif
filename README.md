# Remap SARIF

*Remap SARIF* uses a [source map](https://web.dev/source-maps/) to change line numbers in SARIF files, to map them from the minified or transpiled file locations to the original source file locations.

It accepts input/output SARIF file paths (which can be the same location), as well as an optional root path for the source code.

For any source files that are found to have a source map, it uses that to change the source locations.

This could be useful if a scan has been done on a minified file, or a transpiled file (from high-level languages such as TypeScript, CoffeeScript or Dart, for example, or from a JavaScript framework such as React, Angular, Vue, Svelte, Next.js, etc.).

## Usage as an Action

You must modify an existing Code Scanning Actions workflow file to add the `remap-sarif` action step.

You need to provide the `input` and `output` so that the script knows where to find and put the SARIF.

If the source root isn't the same as the root of the GitHub workspace then you need to provide the `sourceroot` so that the script knows where to find the source files, and their mapping files.

For example, if we are using the CodeQL action, we change the single `analyze` step from this:

```yaml
    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2
```

To:

```yaml
    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2
      with:
        upload: False
        output: sarif-results

    - name: Remap SARIF
      uses: advanced-security/remap-sarif@main
      with:
        sourceroot: src   # optional
        input: sarif-results/${{ matrix.language }}.sarif
        output: sarif-results/${{ matrix.language }}.sarif
      
    - name: Upload SARIF
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: sarif-results/${{ matrix.language }}.sarif
```

Note how we provided `upload: False` and `output: sarif-results` to the `analyze` action. That way we can edit the SARIF with the `remap-sarif` action before uploading it with the `upload-sarif` action.

A full example workflow is:

```yaml
name: "Remap SARIF"
on:
  push:
    branches: [main]

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest

    strategy:
      fail-fast: false
      matrix:
        language: [ 'javascript' ]

    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v2
      with:
        languages: ${{ matrix.language }}

    - name: Autobuild
      uses: github/codeql-action/autobuild@v2

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2
      with:
        upload: False
        output: sarif-results

    - name: Remap SARIF
      uses: advanced-security/remap-sarif@main
      with:
        sourceroot: src   # optional
        input: sarif-results/${{ matrix.language }}.sarif
        output: sarif-results/${{ matrix.language }}.sarif

    - name: Upload SARIF
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: sarif-results/${{ matrix.language }}.sarif

    - name: Upload SARIF results as a Build Artifact
      uses: actions/upload-artifact@v3
      with:
        name: sarif-results
        path: sarif-results
        retention-days: 1
```

In this full example we also attach the resulting SARIF file to the build as a Build Artifact, which is convenient for later inspection. You can remove this step if you don't need it.

## Usage at the command-line

``` bash
python3 remap_sarif.py <sarif file path> <source root> --output=<output sarif file path>
```

## What is a sourcemap?

Sourcemaps are mostly used in the JavaScript ecosystem, to allow pointing to original source file locations when using converted or transpiled source.

## Known issues

* If the source code root isn't the top of the GitHub workspace, then you must provide the "source root" as an argument - it is not extracted from the SARIF file.
* Partial Fingerprints are not remapped to the original source file.
* Mapped locations with relative paths are probably library code, but are not yet removed.

## Requirements

* Python 3.7 or later
or
* GitHub Actions runner

## License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](LICENSE) for the full terms.

## Maintainers

See [CODEOWNERS](CODEOWNERS) for the list of maintainers.

## Support

See the [SUPPORT](SUPPORT.md) file.

## Background

See the [CHANGELOG](CHANGELOG.md), [CONTRIBUTING](CONTRIBUTING.md), [SECURITY](SECURITY.md), [SUPPORT](SUPPORT.md), [CODE OF CONDUCT](CODE_OF_CONDUCT.md) and [PRIVACY](PRIVACY.md) files for more information.
