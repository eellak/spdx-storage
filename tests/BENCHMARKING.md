# Benchmarking `spdx-storage import`

These benchmarks evaluate the performance of the `spdx-storage import` command across all supported triplestore backends.

Before running the benchmarks, the required SPDX sample repositories were
cloned using:
```bash
make all
```

The `all` target in the [Makefile](./Makefile) prepares the benchmark input
files by cloning the [SPDX examples](https://github.com/spdx/spdx-examples) and [SPDX visualizer](https://github.com/kartben/spdx3_viz) repositories.

The complete benchmark dataset contains approximately **1.4 GB** of SPDX
files and represents approximately **15 million RDF
triples**.

The files were processed in ascending order of file size to make the workload
more predictable and to avoid starting with the largest memory-intensive inputs.

Each benchmark was executed with:
```bash
/usr/bin/time -v -o time-{backend}.txt make import-all
```

The `import-all` target repeatedly executes the equivalent of:
```bash
spdx-storage --config-file config.toml import {file}
```

The [config.toml](./config.toml) file specifies the triplestore backend, the target graph (`https://example.org/spdx-test`), and the name of the repository used for storing the imported data. In the case of Oxigraph, the `name` configuration option specifies the persistent storage location instead. The `backend` value was changed for each benchmark run to select the triplestore being evaluated.

The measurements reported below include the total wall-clock execution time,
CPU utilization, and maximum resident set size (peak RSS) reported by
GNU `time`.

## Results

| Backend | Total Time (min:s) | CPU (%) | Peak RSS (GiB) | Notes |
|---|---:|---:|---:|---|
| AllegroGraph | 14:02 | 32 | 0.39 | Yocto6 excluded due to the free-license 5M triple limit |
| Blazegraph | 36:20 | 39 | 0.45 | Full benchmark dataset |
| GraphDB | 37:48 | 29 | 0.45 | Full benchmark dataset |
| Jena | 40:50 | 29 | 0.46 | Full benchmark dataset |
| Oxigraph | 29:11 | 101 | 2.39 | Full benchmark dataset |
| RDF4J | 36:03 | 43 | 0.44 | Full benchmark dataset |
| Virtuoso | 14:05 | 67 | 0.43 | Android sample excluded due to a Virtuoso Turtle parser incompatibility |

> **Note:** For server-based backends, the reported peak RSS corresponds to the
> `spdx-storage` client process and does not include the memory consumed by the
> external triplestore server. Oxigraph runs embedded in the same process, so its
> RSS is not directly comparable to the client-side RSS values of server-based
> backends.

### Environment

- Ubuntu 22.04.2 LTS on WSL2
- Python 3.14.6
- `spdx-storage`: `v0.1.0`
- `rdf-triplestore`: `v0.1.1`
- Memory: 11 GiB RAM, 8 GiB swap