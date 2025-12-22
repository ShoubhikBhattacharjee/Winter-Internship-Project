# Python Data Structures: Lists vs. Tuples

## Lists `[]`
Lists are ordered collections that are **mutable**. This means you can add, remove, or change items after the list has been created.
- **Syntax:** `my_list = [1, 2, 3]`
- **Use Case:** Use a list when you have a collection of data that needs to be modified frequently.
- **Performance:** Slightly slower than tuples because they require more memory to allow for changes.

## Tuples `()`
Tuples are ordered collections that are **immutable**. Once a tuple is created, you cannot change its contents.
- **Syntax:** `my_tuple = (1, 2, 3)`
- **Use Case:** Use a tuple for data that should not change (like coordinates or configuration settings). This protects the data from accidental modification.
- **Performance:** Faster and more memory-efficient than lists.

## Comparison Table
| Feature | List | Tuple |
| :--- | :--- | :--- |
| **Mutability** | Mutable (Can change) | Immutable (Cannot change) |
| **Syntax** | `[item1, item2]` | `(item1, item2)` |
| **Size** | Larger memory footprint | Smaller memory footprint |
| **Methods** | Many (append, remove, pop) | Few (count, index) |