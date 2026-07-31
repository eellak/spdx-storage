# High-level interface description

This is a command-line utility designed to facilitate the management and manipulation of SPDX data.
It provides a set of commands that allow users to perform various operations
such as reading, writing, transforming, and analyzing data in a streamlined manner.
The utility is built with a focus on usability, efficiency, and flexibility,
making it suitable for both novice and experienced users.

The different available commands are listed below,
allowing users to easily navigate and read about the provided features.
Each command comes with a set of options and parameters that can be customized to fit specific use cases.

## `config`

```sh
spdx-storage config [OPTIONS] SUBCOMMAND [ARGS]...
```

This command is modeled after the `git config` command and is used to manage configuration settings for the utility.

The optional [OPTIONS] before the SUBCOMMAND can be used to specify the configuration file to be used (e.g., `--config-file <path>`), allowing users to customize their settings and have multiple configuration files if needed.

The configuration settings can be stored in a configuration file, allowing users to persist their preferences across sessions.

### Configuration File Location
By default the configuration file is located in the user's home directory, but this can be customized using the `--config-file` option.
The default location depends on the operating system (the Python module `platformdirs` is used to determine the appropriate location).

### Subcommands
The available subcommands are:

* `spdx-storage config set <key> <value>`: sets a configuration key to a specified value.
* `spdx-storage config get <key>`: retrieves the value of a specified configuration key.
* `spdx-storage config list`: provides a list of all configuration keys and their corresponding values.

### Keys
The available configuration keys are:

* `backend`: specifies the backend to be used for storage (e.g., `sqlite`, `postgresql`, etc.).
* `graph`: specifies the name of the graph inside the database, allowing for disjoint graphs.
* `conn_url`: specifies the URL of the database connection.
* `auth`: specifies the authentication payload to be used for the database connection.

Not all keys are meaningful for all backends, and some backends may require additional keys to be set.

## `import`

```sh
spdx-storage import [OPTIONS] <input_file>
```

This command is used to save (import) SPDX data from an external file into the storage system.

The optional [OPTIONS] can be used to specify the configuration file to be used (i.e., `--config-file <path>`).

The file should contain valid SPDX data in a supported format (e.g., JSON, RDF, etc.),
and the utility will parse the data and store it in the specified backend.

## `import-sbom`

```sh
spdx-storage import-sbom [OPTIONS] <input_file>
```

This command is used to save (import) an SPDX SBOM from an external file into the storage system.

The optional [OPTIONS] can be used to specify the configuration file to be used (i.e., `--config-file <path>`).

The file should contain a valid SPDX SBOM in a supported format (e.g., JSON, RDF, etc.),
and the utility will parse the data and store it in the specified backend.

Other available options include:

* `--check`: This option allows users to perform a validation check on the SPDX SBOM before saving it to the storage system. If the SBOM is invalid, an error message will be displayed, and the import operation will be aborted.

## `export`

```sh
spdx-storage export [OPTIONS] <id>
```

This command is used to export SPDX data from the storage system.

The optional [OPTIONS] can be used to specify the configuration file to be used (i.e., `--config-file <path>`).

### Export Scope
This command exports the SPDX data of an `<id>`, together with all other data connected to it,
since this is the most common use case for exporting data.
If one wants to export only a specific part of the data, they can use the `--only` option to specify that only data about `<id>` should be exported.

### Output Location
By default the export command will output the data to the standard output (stdout),
but users can redirect the output to a file using shell redirection (e.g., `spdx-storage export <id> > output.json`)
or use the `--output` option to specify an output file (e.g., `--output <output_file>`).

### Output Format
By default the exported data will be in JSON-LD format,
but users can specify a different format using the `--format` option (e.g., `--format nt`).
