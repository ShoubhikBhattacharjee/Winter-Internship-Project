# Database Comparison: SQL vs. NoSQL

Choosing the right database depends on the structure of your data and how you plan to scale.



## SQL (Relational Databases)
SQL databases use a structured query language and have a predefined schema.
- **Structure:** Data is stored in tables with rows and columns.
- **Scaling:** Usually **Vertically** (adding more power like CPU/RAM to a single server).
- **Properties:** Follows **ACID** (Atomicity, Consistency, Isolation, Durability) properties for reliable transactions.
- **Examples:** PostgreSQL, MySQL, Microsoft SQL Server, Oracle.

## NoSQL (Non-Relational Databases)
NoSQL databases have dynamic schemas for unstructured data.
- **Structure:** Data can be stored as Documents (JSON), Key-Value pairs, Graphs, or Wide-columns.
- **Scaling:** Usually **Horizontally** (adding more servers to a cluster).
- **Properties:** Follows the **CAP theorem** (Consistency, Availability, Partition Tolerance).
- **Examples:** MongoDB (Document), Redis (Key-Value), Cassandra (Wide-column), Neo4j (Graph).

## Comparison Summary
| Feature | SQL | NoSQL |
| :--- | :--- | :--- |
| **Schema** | Fixed / Predefined | Dynamic / Flexible |
| **Data Storage** | Table-based | Document, Key-value, Graph |
| **Best For** | Multi-row transactions | Large sets of distributed data |
| **Queries** | Complex (JOINs) | Focused on high-speed retrieval |