# Remap SARIF

*Remap SARIF* accepts a SARIF file and a source root.

For any source files that are found to have a sourcemap, it uses that to change the source locations.

This could be useful if a scan has been done on a minified file, or a transpiled file (from TypeScript or Dart, for example).

## Usage

``` bash
./remap_sarif.py <sarif file path> <source root>
```

## What is a sourcemap?

Sourcemaps are mostly used in the JavaScript ecosystem, to allow pointing to original source file locations when using converted or transpiled source.

## Known issues

You must provide the "source root" as an argument - it is not extracted from the SARIF file.

Partial Fingerprints are not remapped to the original source file.

Non-mapped locations in the SARIF are not remapped and are left unchanged.

No mapped locations with relative paths (probable library code) are removed.
