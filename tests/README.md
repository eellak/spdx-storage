# Testing `spdx-storage`
This directory contains SPDX example files that can be used to test the `spdx-storage` command-line interface.

The example below shows how to import SPDX data into a configured storage system using the CLI.

## Importing an SPDX file
Before importing SPDX data, `spdx-storage` needs to know which storage implementation to use and where the data should be stored. These settings are provided through a configuration file.

The example below uses Oxigraph as a simple storage backend:

`config.toml`:
```toml
backend = "oxigraph"
graph = "https://example.org/spdx"
```
Here, `backend` selects the storage implementation and `graph` identifies the RDF graph where the imported SPDX data will be stored.

More information about the available configuration options can be found [here](../docs/description.md)

An SPDX file can then be imported using the CLI:
```bash
spdx-storage --config-file config.toml import tests/example1.spdx3.json
```
The `--config-file` option tells `spdx-storage` which storage configuration to use and must be specified before the import command.

If no `--config-file` is provided, `spdx-storage` uses its default configuration file.

During import, the SPDX file is parsed and its data is stored in the configured backend.

### Supported input formats
The import command currently supports the following file extensions:
- `.jsonld`
- `.spdx.json`
- `.spdx3.json`
- `.ttl`
- `.turtle`
- `.nt`
- `.xml`
