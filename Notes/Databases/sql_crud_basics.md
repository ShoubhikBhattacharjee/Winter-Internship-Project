# SQL Fundamentals: CRUD Operations

## Introduction to SQL
SQL (Structured Query Language) is the domain-specific language used for interacting with Relational Database Management Systems (RDBMS) like MySQL, PostgreSQL, and SQL Server.

## The CRUD Acronym
CRUD describes the four essential operations for managing persistent data elements.

### 1. Create (INSERT)
Used to add new data records into a table.
- **Example:** `INSERT INTO Students (ID, Name) VALUES (1, 'Shoubhik');`

### 2. Read (SELECT)
Used to retrieve data from one or more tables. It is the most common SQL command.
- **Example:** `SELECT * FROM Students WHERE ID = 1;`

### 3. Update (UPDATE)
Used to modify existing data records within a table.
- **Example:** `UPDATE Students SET Name = 'S. Bhattacharjee' WHERE ID = 1;`

### 4. Delete (DELETE)
Used to remove specific records from a table.
- **Example:** `DELETE FROM Students WHERE ID = 1;`

## Importance in RAG
In a Retrieval-Augmented Generation (RAG) system, SQL is often used to filter metadata or retrieve structured context that helps the AI model generate more grounded and accurate responses.s