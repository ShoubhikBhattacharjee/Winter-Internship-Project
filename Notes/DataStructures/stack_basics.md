# Data Structures: The Stack

A Stack is a collection of elements where addition and removal happen at the same end, called the "top."



## The LIFO Principle
LIFO stands for **Last-In, First-Out**. 
- Imagine a stack of dinner plates. You put the last plate on the top, and when you need one, you take it from the top.
- You cannot take the bottom plate without removing all the ones above it first.

## Core Operations
1. **Push**: Adding an element to the top of the stack.
2. **Pop**: Removing the top element from the stack.
3. **Peek (or Top)**: Looking at the top element without removing it.
4. **isEmpty**: Checking if the stack has any elements.

## Real-World Examples
- **Undo Mechanism:** In software like VS Code or Word, your last action is "pushed" onto a stack. When you hit `Ctrl+Z`, the last action is "popped" and reversed.
- **Browser History:** When you visit a new page, it’s pushed onto the stack. When you hit "Back," the current page is popped off.
- **Function Calls:** Programming languages use a "Call Stack" to keep track of which function is currently running.