#!/usr/bin/env python3

import argparse
from dataclasses import replace
import json
import logging
import os
from textwrap import indent
import sourcemap

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def add_args(parser):
    """Add arguments to command line parser."""
    parser.add_argument('sarif', help="A SARIF file to remap with a sourcemap")
    parser.add_argument('sourceroot', help="The source root for the SARIF file")


class Mapper:
    def __init__(self, sourceroot) -> None:
        self.root = sourceroot
        self.cache = {}

    def remap(self, filepath, line, col) -> tuple[str, int, int]:
        if filepath in self.cache:
            smap = self.cache["file"]
        else:
            try:
                map_file = sourcemap.discover(open(os.path.join(self.root, filepath)).read())
            except IOError as err:
                raise IndexError("Mapping not found: %s", err)
            if map_file is not None:
                with open(os.path.join(self.root, map_file)) as f:
                    smap = sourcemap.load(f)
                    self.cache["file"] = smap
            else:
                raise IndexError(f"Mapping not found: map file for {filepath} not found")
        try:
            loc = smap.lookup(line, col)
        except IndexError as err:
            raise IndexError(f"Mapping not found: {filepath}!{line}:{col} not found")
        return (loc.name, loc.src, loc.src_line, loc.src_col)



def main():
    """Main entry point for the application script."""
    parser = argparse.ArgumentParser(description='Process sourcemap')
    add_args(parser)
    args = parser.parse_args()

    sarif_file = args.sarif
    mapper = Mapper(args.sourceroot)

    sarif = json.load(open(sarif_file))

    try:
        for run in sarif["runs"]:
            artifacts = run["artifacts"]
            replaced_artifacts = set()

            for result in run["results"]:
                for location in result["locations"]:
                    uri = location["physicalLocation"]["artifactLocation"]["uri"]
                    region = location["physicalLocation"]["region"]

                    try:
                        startline = region["startLine"]
                        startcol = region["startColumn"]
                        name, src, src_line, src_col = mapper.remap(
                            uri, startline, startcol
                        )

                        LOG.debug("Found mapping to %s @ %s!%s:%s for %s!%s:%s", name, src, src_line, src_col, uri, startline, startcol)

                        if src is not None:
                            location["physicalLocation"]["artifactLocation"]["uri"] = src
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
                        endline = region["endLine"] if "endLine" in region else startline
                        endcol = region["endColumn"] if "endColumn" in region else startcol
                        name, src, src_line, src_col = mapper.remap(
                            uri, endline, endcol
                        )

                        LOG.debug("Found mapping to %s @ %s!%s:%s for %s!%s:%s", name, src, src_line, src_col, uri, endline, endcol)

                        if src is not None:
                            region["endLine"] = src_line
                            region["endColumn"] = src_col
                    except IndexError as err:
                        LOG.warning("Index error: %s", err)
    except KeyError as err:
        LOG.warning("Malformed SARIF, expected key missing: %s", err)

    print(json.dumps(sarif, indent=2))


if __name__ == "__main__":
    main()
