# Overview

`spdx-storage` is a command-line tool for storing, importing, exporting, and managing SPDX data.

It is designed to make SPDX data easier to work with by providing a consistent workflow for loading SPDX documents, storing their RDF representation, and retrieving related SPDX information when needed (e.g. by id).

The tool supports configuration of the storage backend, importing SPDX documents into storage, and exporting SPDX data starting from a selected entity id. Internally, it uses the `triplestore` library to interact with different RDF triplestore implementations without exposing backend-specific details to the user.

# CLI commands

## `config`
The `config` command is used to manage the configuration settings used by `spdx-storage`.

It follows a workflow similar to `git config`, allowing configuration values to be stored, retrieved, and listed from the command line.

### Usage
```sh
spdx-storage [OPTIONS] config SUBCOMMAND [ARGS]...
```
Where:

- `[OPTIONS]` specifies additional command-line settings for `spdx-storage`, such as `--config-file <path>` for selecting a custom configuration file.
- `SUBCOMMAND` specifies the configuration operation to perform. Available subcommands are `set`, `get`, and `list`.
- `[ARGS]` are the arguments required by the selected subcommand.


### Configuration file

Configuration values are persisted in a configuration file and reused across commands.

By default, `spdx-storage` uses the configuration file location determined by `platformdirs`, so the exact path depends on the operating system.

A custom configuration file can be selected with the `--config-file` option. This can be useful when maintaining separate configurations for different backend instances or environments.

Example:
```sh
spdx-storage --config-file ./config.toml config list
```

### Subcommands
`set`

Sets a configuration value
```sh
spdx-storage config set <key> <value>
```
Example:
```sh
spdx-storage config set backend oxigraph
spdx-storage config set graph https://example.org/spdx
```

If a custom configuration file is required:
```sh
spdx-storage --config-file ./config.toml config set backend oxigraph
```

`get`

Returns the value associated with a configuration key
```sh
spdx-storage config get <key>
```
Example:
```sh
spdx-storage config get backend
```

`list`

Lists the configuration values currently stored in the selected configuration file
```sh
spdx-storage config list
```

### Configuration keys
The following configuration keys are supported:
| Key | Description |
| --- | --- |
| `backend` | Backend used for storing SPDX data. |
| `name` | Optional name used by backends that require or support a named store or repository. |
| `graph` | RDF graph in which SPDX data is stored. |
| `conn_url` | Connection URL used to access the configured backend. |
| `auth` | Authentication information required by the backend. |

Not every configuration key is required by every backend. The exact set of values needed depends on the selected backend.

Example configuration:

A simple local configuration using the [Oxigraph](https://github.com/oxigraph/oxigraph) triplestore backend may contain:
```toml
backend = "oxigraph"
graph = "https://example.org/spdx"
```

The same configuration is used by commands such as `import` and `export` when they initialize the storage backend.

## `import`

The `import` command is used to load SPDX data from an external file into the configured storage backend.

The input file is parsed as RDF data and all resulting triples are added to the configured storage backend.

### Usage
```sh
spdx-storage [OPTIONS] import <input_file>
```
Where:
- `[OPTIONS]` specifies additional command-line settings for `spdx-storage`, such as `--config-file <path>` for selecting a custom configuration file.
- `<input_file>` is the path to the SPDX file to import.

Example:
```sh
spdx-storage import ./example.spdx.json
```
Using a custom configuration file:
```sh
spdx-storage --config-file ./config.toml import ./example.spdx.json
```

### Input file
The input path must point to an existing file containing SPDX data serialized in one of the supported RDF formats.

The input format is detected automatically from the file extension.

### Supported formats
| Format | File extension |
| --- | --- |
| JSON-LD | `.json`, `.jsonld`, `.json-ld` |
| Turtle | `.ttl`, `.turtle` |
| N-Triples | `.nt` |
| RDF/XML | `.rdf`, `.xml` |

Files with unsupported extensions are rejected before the import is performed.

### Import process
When an SPDX file is imported, `spdx-storage`:

1. verifies that the input path exists and points to a file;
2. resolves the configuration file;
3. detects the RDF format from the input file extension;
4. parses the input file into an RDF graph;
5. initializes the configured storage backend; and
6. adds all parsed triples to the configured graph.

The storage backend is initialized using the configuration values described in the [config](#configuration-keys) section, including `backend`, `name`, `graph`, `conn_url`, and `auth` when available.

### Errors
The import command fails if:
- the input path does not exist or does not point to a file;
- an explicitly provided configuration file does not exist or is not a file;
- the input file extension is not supported; or
- the input file cannot be parsed in the detected RDF format.