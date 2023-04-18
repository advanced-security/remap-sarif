#!/usr/bin/env python3
"""Remap a SARIF file to original source file locations with source maps."""

import sys
import argparse
import json
import logging
import os
import sourcemap

LOG = logging.getLogger(__name__)


def add_args(parser):
    """Add arguments to command line parser."""
    parser.add_argument('sarif', help="A SARIF file to remap with sourcemaps")
    parser.add_argument('sourceroot', help="The source root for the SARIF file")
    parser.add_argument('--output',
                        required=False,
                        help="The output SARIF file to write to")
    parser.add_argument('--debug',
                        '-d',
                        action="store_true",
                        help="Debug output on")


class Mapper:
    """Remap source file locations with a source root and a cache of source maps."""

    def __init__(self, sourceroot) -> None:
        self.root = sourceroot
        self.cache: dict[str, sourcemap.objects.SourceMapIndex] = {}

    def remap(self, filepath, line, col) -> tuple[str, str, int, int]:
        """Remap the locations."""
        if filepath in self.cache:
            smap = self.cache["file"]
        else:
            try:
                map_file = sourcemap.discover(
                    open(os.path.join(self.root, filepath)).read())
            except IOError as err:
                raise IndexError("Mapping error: %s", err)
            if map_file is not None:
                with open(os.path.join(self.root, map_file)) as f:
                    smap = sourcemap.load(f)
                    self.cache["file"] = smap
            else:
                raise IndexError(
                    f"Mapping error: map file for {filepath} not found")
        try:
            loc = smap.lookup(line, col)
        except IndexError:
            raise IndexError(
                f"Mapping error: {filepath}!{line}:{col} not found")
        return (loc.name, loc.src, loc.src_line, loc.src_col)


def main():
    """Main entry point for the application script."""
    parser = argparse.ArgumentParser(description='Process sourcemap')
    add_args(parser)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.debug:
        LOG.setLevel(logging.DEBUG)

    sarif_file = args.sarif
    mapper = Mapper(args.sourceroot)

    with open(sarif_file, "r") as f:
        sarif = json.load(f)

    try:
        for run in sarif["runs"]:
            artifacts = run["artifacts"]
            replaced_artifacts = set()

            for result in run["results"]:
                for location in result["locations"]:
                    uri = location["physicalLocation"]["artifactLocation"][
                        "uri"]
                    region = location["physicalLocation"]["region"]

                    try:
                        startline = region["startLine"]
                        startcol = region["startColumn"]

                        name, src, src_line, src_col = mapper.remap(
                            uri, startline, startcol)

                        LOG.debug("Found mapping to %s @ %s!%s:%s for %s!%s:%s",
                                  name, src, src_line, src_col, uri, startline,
                                  startcol)

                        if src is not None:
                            location["physicalLocation"]["artifactLocation"][
                                "uri"] = src

                            region["startLine"] = src_line
                            region["startColumn"] = src_col

                            if uri not in replaced_artifacts:
                                for artifact in artifacts:
                                    if artifact["location"]["uri"] == uri:
                                        artifact["location"]["uri"] = src
                                        replaced_artifacts.add(uri)

                    except IndexError as err:
                        LOG.warning("Index error: %s", err)

                    try:
                        endline = region[
                            "endLine"] if "endLine" in region else startline
                        endcol = region[
                            "endColumn"] if "endColumn" in region else startcol

                        name, src, src_line, src_col = mapper.remap(
                            uri, endline, endcol)

                        LOG.debug("Found mapping to %s @ %s!%s:%s for %s!%s:%s",
                                  name, src, src_line, src_col, uri, endline,
                                  endcol)

                        if src is not None:
                            region["endLine"] = src_line
                            region["endColumn"] = src_col
                    except IndexError as err:
                        LOG.warning("Index error: %s", err)
    except KeyError as err:
        LOG.warning("Malformed SARIF, expected key missing: %s", err)

    # note: closes STDOUT if we're writing to there
    with open(args.output, "w") if args.output else sys.stdout as f:
        print(json.dumps(sarif, indent=2), file=f)


if __name__ == "__main__":
    main()
