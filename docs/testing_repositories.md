# Edge-Case Repositories For Pull Request Testing

Use this list when a pull request needs manual validation against repositories
with different data shapes. Add a short reason whenever a new edge case appears.

| Repository | Why it is useful |
| --- | --- |
| `rook/rook` | Large infrastructure project with dependency/package metadata gaps. |
| `kubernetes/kubernetes` | Very large history and high contributor volume. |
| `ansible/ansible` | Mixed issue and pull request activity across a long history. |
| `chaoss/augur` | Closely related data model for schema-dependent query changes. |
| `openssl/openssl` | Security-heavy project with release and maintenance lifecycle signals. |
| `curl/curl` | Long-lived C project with broad release history and active maintainers. |
| `pallets/flask` | Smaller Python project with clearer package metadata. |
| `nodejs/node` | Large JavaScript/C++ project with release-line lifecycle data. |
| `rust-lang/rust` | High-volume project with labels, teams, and fast issue movement. |
| `prometheus/prometheus` | Go service project with well-structured releases and dependencies. |

For visualization changes, test at least one large repository and one smaller
repository so empty states, slow queries, and dense charts are all exercised.
