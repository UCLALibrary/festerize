#!/usr/bin/env python

from datetime import datetime
from enum import IntEnum
import logging
import os
import pathlib
import pkg_resources
import random
import sys

from bs4 import BeautifulSoup
import click
import requests


@click.command()
@click.argument("src", nargs=-1)
@click.option(
    "--iiif-api-version",
    "-v",
    type=click.Choice(["2", "3"]),
    required=True,
    help="""IIIF Presentation API version that Fester should use.

Version 3 may be used for content intended to be viewed exclusively with
Mirador 3.

For all other cases, version 2 should be used, especially for any content
intended to be viewed with Universal Viewer.""",
)
@click.option(
    "--server",
    default="https://ingest.iiif.library.ucla.edu",
    show_default=True,
    help="URL of the Fester service dedicated for ingest",
)
@click.option(
    "--out",
    default="output",
    show_default=True,
    help="local directory to put the updated CSV",
)
@click.option(
    "--iiifhost", default=None, help="IIIF image server URL (optional)",
)
@click.option(
    "--metadata-update",
    "-m",
    is_flag=True,
    help="Only update manifest (work) metadata; don't update canvases (pages).",
)
@click.option(
    "--strict-mode",
    is_flag=True,
    help="""Festerize immediately exits with an error code if Fester responds
with an error, or if a user specifies on the command line a file that does not
exist or a file that does not have a .csv filename extension. The rest of the
files on the command line (if any) will remain unprocessed.""",
)
@click.option(
    "--loglevel",
    type=click.Choice(["INFO", "DEBUG", "ERROR"]),
    default="INFO",
    show_default=True,
)
@click.version_option(prog_name="Festerize", message="%(prog)s v%(version)s")
def festerize(
    src,
    iiif_api_version,
    server,
    out,
    iiifhost,
    metadata_update,
    strict_mode,
    loglevel,
):
    """Uploads CSV files to the Fester IIIF manifest service for processing.

    Any rows with an `Object Type` of `Collection` (i.e., "collection row")
    found in the CSV are used to create a IIIF collection.

    Any rows with an `Object Type` of `Work` (i.e., "work row") are used to
    expand or revise a previously created IIIF collection (corresponding to
    the collection that the work is a part of), as well as create a IIIF
    manifest corresponding to the work. A "work" is conceived of as a discrete
    object (e.g., a book or a photograph) that one would access as an
    individual item.

    Any rows with an `Object Type` of `Page` (i.e., "page row") are likewise
    used to expand or revise a previously created IIIF manifest (corresponding
    to the work that the page is a part of), unless the `--metadata-update`
    flag is used (in which case, page rows are ignored).

    After Fester creates or updates any IIIF collections or manifests, it
    updates and returns the CSV files to the user.

    The returned CSVs are updated to contain URLs (in a `IIIF Manifest URL`
    column) of the IIIF collections and manifests that correspond to any
    collection or work rows found in the CSV.

    Note that the order of operations is important. The following will result
    in an error:

        1. Running `festerize` with a CSV containing works that are part of a
        collection for which no IIIF collection has been created (i.e., the
        work's corresponding collection hasn't been festerized yet)

            - Solution: add a collection row to the CSV and re-run `festerize`
            with it, or run `festerize` with another CSV that contains the
            collection row

        2. Running `festerize` with a CSV containing pages that are part of a
        work for which no IIIF manifest has been created (i.e., the page's
        corresponding work hasn't been festerized yet)

            - Solution: add a work row to the CSV and re-run `festerize` with
            it, or run `festerize` with another CSV that contains the work row

    Arguments:

        SRC is either a path to a CSV file or a Unix-style glob like '*.csv'.
    """

    class FesterizeError(IntEnum):

        """Exit codes used by the program."""

        NO_FILES_SPECIFIED = 1
        NONEXISTENT_FILE_SPECIFIED = 2
        NON_CSV_FILE_SPECIFIED = 3
        FESTER_UNAVAILABLE = 4
        FESTER_ERROR_RESPONSE = 5
        FILE_IO_ERROR = 6

    festerize_version = pkg_resources.require("Festerize")[0].version

    if len(src) == 0:
        click.echo("Please provide one or more CSV files", err=True)
        sys.exit(FesterizeError.NO_FILES_SPECIFIED)

    if not os.path.exists(out):
        click.echo("Output directory {} not found, creating it.".format(out))
        os.makedirs(out)
    else:
        click.confirm(
            "Output directory {} found, should we continue? YES might overwrite any existing output files.".format(
                out
            ),
            abort=True,
        )

    # Logging setup.
    started = datetime.now()
    logfile_path = os.path.join(
        out, "{}.log".format(started.strftime("%Y-%m-%d--%H-%M-%S"))
    )
    logging.basicConfig(
        filename=logfile_path,
        filemode="w",
        level=loglevel,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    extra_satisfaction = ["🎉", "🎊", "✨", "💯", "😎", "✔️ ", "👍"]

    logging.info("STARTING at {}...".format(started.strftime("%Y-%m-%d %H:%M:%S")))

    # HTTP request URLs.
    get_status_url = server + "/fester/status"
    post_csv_url = server + "/collections"

    # HTTP request headers.
    request_headers = {"User-Agent": "{}/{}".format("Festerize", festerize_version)}

    # If Fester is unavailable, abort.
    try:
        s = requests.get(get_status_url, headers=request_headers)
        s.raise_for_status()
    except requests.exceptions.RequestException as e:
        error_msg = "Fester IIIF manifest service unavailable: {}".format(str(e))
        click.echo(error_msg, err=True)
        logging.error(error_msg)
        sys.exit(FesterizeError.FESTER_UNAVAILABLE)

    for pathstring in src:
        csv_filepath = pathlib.Path(pathstring)
        csv_filename = csv_filepath.name

        if not csv_filepath.exists():
            error_msg = "File {} does not exist".format(csv_filename)
            click.echo(error_msg, err=True)
            logging.error(error_msg)

            if strict_mode:
                sys.exit(FesterizeError.NONEXISTENT_FILE_SPECIFIED)

        # Only works with CSV files that have the proper extension.
        elif csv_filepath.suffix == ".csv":
            click.echo("Uploading {} to {}".format(csv_filename, post_csv_url))

            # Upload the file.
            files = {
                "file": (
                    pathstring,
                    open(pathstring, "rb"),
                    "text/csv",
                    {"Expires": "0"},
                )
            }
            payload = [("iiif-version", "v{}".format(iiif_api_version))]
            if iiifhost is not None:
                payload.append(("iiif-host", iiifhost))
            if metadata_update:
                payload.append(("metadata-update", True))
            r = requests.post(
                post_csv_url, headers=request_headers, files=files, data=payload
            )

            # Handle the response.
            if r.status_code == 201:
                click.echo("Uploaded {} successfully".format(csv_filename))

                # Check the returned CSV
                content_length_header_key = "Content-Length"
                click.echo(
                    "{}: {}".format(
                        content_length_header_key, r.headers[content_length_header_key]
                    )
                )

                # Save the result CSV to the output directory.
                with open(os.path.join(out, csv_filename), "wb") as f:
                    num_bytes_written = f.write(r.content)

                if num_bytes_written is 0:
                    error_msg = "Failed to write data to {}".format(csv_filename)
                    click.echo(error_msg, err=True)
                    logging.error(error_msg)

                    if strict_mode:
                        sys.exit(FesterizeError.FILE_IO_ERROR)
                else:
                    # Send an awesome message to the user.
                    border_char = extra_satisfaction[
                        random.randint(0, len(extra_satisfaction) - 1)
                    ]
                    border_length = (4 + 10) // 2

                    click.echo(border_char * border_length)
                    click.echo("{} SUCCESS! {}".format(border_char, border_char))
                    click.echo(border_char * border_length)
            else:
                error_page_soup = BeautifulSoup(r.text, features="html.parser")
                try:
                    # Fester error page via Vert.x
                    error_cause = error_page_soup.find(id="error-message").get_text()
                except AttributeError:
                    # nginx error page with response status code and message in title
                    error_cause = "{} - {}".format(
                        error_page_soup.title.string, "nginx"
                    )

                error_msg = "Failed to upload {}: {} (HTTP {})".format(
                    csv_filename, error_cause, r.status_code
                )
                click.echo(error_msg, err=True)
                logging.error(error_msg)

                if strict_mode:
                    sys.exit(FesterizeError.FESTER_ERROR_RESPONSE)
        else:
            error_msg = "File {} is not a CSV".format(csv_filename)
            click.echo(error_msg, err=True)
            logging.error(error_msg)

            if strict_mode:
                sys.exit(FesterizeError.NON_CSV_FILE_SPECIFIED)

    logging.info("DONE at {}.".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
