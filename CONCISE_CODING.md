# Writing Concise Code

## Core Principles

1. **One Purpose, One Function**
   - Each function should do exactly one thing
   - If you can't describe it in one sentence, split it

2. **Meaningful Names**
   - Use clear, descriptive names
   - Avoid abbreviations unless universally known
   - Example: `getUserData()` vs `getData()`

3. **DRY (Don't Repeat Yourself)**
   ```python
   # Instead of:
   if condition:
       print("Processing...")
       do_something()
       print("Done!")
   if other_condition:
       print("Processing...")
       do_other_thing()
       print("Done!")

   # Do this:
   def process_task(task):
       print("Processing...")
       task()
       print("Done!")
   ```

4. **Eliminate Dead Code**
   - Remove commented-out code
   - Delete unused variables
   - Remove redundant comments

5. **Smart Comments**
   - Don't comment on what the code does
   - Comment on why the code does it
   - You can comment code if it makes sense to do so. 

## Code Examples

### ❌ Verbose
```python
def calculate_total_price(items, tax_rate, discount):
    # Initialize total
    total = 0
    # Loop through each item
    for item in items:
        # Get item price
        price = item.get_price()
        # Add to total
        total = total + price
    # Calculate tax
    tax = total * tax_rate
    # Apply discount
    final_total = (total + tax) * (1 - discount)
    # Return the result
    return final_total
```

### ✅ Concise
```python
def calculate_total_price(items, tax_rate, discount):
    subtotal = sum(item.get_price() for item in items)
    return subtotal * (1 + tax_rate) * (1 - discount)
```

## Remember
- Less code = less bugs
- Clarity > cleverness
- If you can remove it without losing meaning, remove it
