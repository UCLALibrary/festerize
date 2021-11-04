# Festerize
[![build status](https://github.com/uclalibrary/festerize/workflows/Tests%20%26%20Code%20Style/badge.svg)](https://github.com/UCLALibrary/festerize/actions)

Uploads CSV files to the Fester IIIF manifest service for processing.

Any rows with an `Object Type` of `Collection` (i.e., "collection row") found in the CSV are used to create a IIIF collection.

Any rows with an `Object Type` of `Work` (i.e., "work row") are used to expand or revise a previously created IIIF collection (corresponding to the collection that the work is a part of), as well as create a IIIF manifest corresponding to the work. A "work" is conceived of as a discrete object (e.g., a book or a photograph) that one would access as an individual item.

Any rows with an `Object Type` of `Page` (i.e., "page row") are likewise used to expand or revise a previously created IIIF manifest (corresponding to the work that the page is a part of), unless the `--metadata-update` flag is used (in which case, page rows are ignored).

After Fester creates or updates any IIIF collections or manifests, it updates and returns the CSV files to the user.

The returned CSVs are updated to contain URLs (in a `IIIF Manifest URL` column) of the IIIF collections and manifests that correspond to any collection or work rows found in the CSV.

Note that the order of operations is important. The following will result in an error:

1. Running `festerize` with a CSV containing works that are part of a collection for which no IIIF collection has been created (i.e., the work's corresponding collection hasn't been festerized yet)

    - **Solution**: add a collection row to the CSV and re-run `festerize` with it, or run `festerize` with another CSV that contains the collection row

1. Running `festerize` with a CSV containing pages that are part of a work for which no IIIF manifest has been created (i.e., the page's corresponding work hasn't been festerized yet)

    - **Solution**: add a work row to the CSV and re-run `festerize` with it, or run `festerize` with another CSV that contains the work row

## Installation

First, ensure that you have Bash, cURL, Python 3.6+ and Pip installed on your system.

**If you are using macOS, your Python must be installed using Pyenv.** See [here](https://github.com/pyenv/pyenv#installation) for installation instructions. Once Pyenv is installed, use it like so:

    pyenv install 3.9.4 # the latest as of this writing

When that's done, run the following command in your shell to install the latest release of Festerize:

    bash <(curl -sSL \
      https://raw.githubusercontent.com/UCLALibrary/festerize/main/install.sh)

## Usage

After it's installed, you can see the available options by running:

    festerize --help

When you do this, you should see the following:

```
Usage: festerize [OPTIONS] [SRC]...

  Uploads CSV files to the Fester IIIF manifest service for processing.

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

Options:
  -v, --iiif-api-version [2|3]   IIIF API version that Fester should use
                                 [required]

  --server TEXT                  URL of the Fester service dedicated for
                                 ingest  [default:
                                 https://ingest.iiif.library.ucla.edu]

  --out TEXT                     local directory to put the updated CSV
                                 [default: output]

  --iiifhost TEXT                IIIF image server URL (optional)
  -m, --metadata-update          Only update manifest (work) metadata; don't
                                 update canvases (pages).

  --strict-mode                  Festerize immediately exits with an error
                                 code if Fester responds with an error, or if
                                 a user specifies on the command line a file
                                 that does not exist or a file that does not
                                 have a .csv filename extension. The rest of
                                 the files on the command line (if any) will
                                 remain unprocessed.

  --loglevel [INFO|DEBUG|ERROR]  [default: INFO]
  --version                      Show the version and exit.
  --help                         Show this message and exit.
```

The SRC argument supports standard [filename globbing](https://en.wikipedia.org/wiki/Glob_(programming)) rules. In other words, `*.csv` is a valid entry for the SRC argument.

*There are limits* to how many arguments can be sent to a command. This depends on your OS and its configuration. See this [StackExchange](https://unix.stackexchange.com/questions/110282/cp-max-source-files-number-arguments-for-copy-utility) post for more information.

Festerize will ignore any files that do not end with `.csv`, so a command of `festerize *.*` should be safe to run. Festerize does not recursively search folders.

Festerize creates a folder (by default called `./output`) for all output. CSVs returned by the Fester service are stored there, with the same name as the SRC file.

Festerize also creates a log file in the output folder, named the current date and time of the run, with an extension of `.log`. By default, the start and end time of the run are added as INFO rows to this log file, but this can be disabled by setting the `--loglevel` option to `--loglevel ERROR`.

## Development

It is recommended that developers create a virtual environment for local Python development. After cloning the repository, here's a quick way to get setup:

    #!/bin/bash

    python3 -m venv venv_festerize
    . venv_festerize/bin/activate
    pip install -e . "black>=19.*,<20.*" pytest

To run the tests:

    pytest

Before pushing, make sure you format all the Python source files:

    black *.py

To run the `festerize` executable for manual testing:

    ./venv_festerize/bin/festerize --help

## Releases

To create a new release:

1. Update the version number in `setup.py`.
1. Push a new Git tag using the new version number:
    ```
    #!/bin/bash

    NEXT_VERSION=0.1.0
    git tag -s $NEXT_VERSION -m "Tagging \"$NEXT_VERSION\" for release"
    git push origin $NEXT_VERSION
    ```
1. Create a new release using the GitHub UI.

## Contact

Feel free to use this project's [issues queue](https://github.com/uclalibrary/festerize/issues) to ask questions, make suggestions, or provide other feedback.
