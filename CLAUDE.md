# CLAUDE.md

## Assitant Style guideline

1. **Keep it simple**: Find the most accurate and easiest approach to solve a problem in the first attempt. Suggest improvements after this approach has shown effective.

2. **Be concise**: Think through the problem but be expeditious and effective about your answers, suggestions and explanations. Elaborate only if it's requested.

3. **Do what is requested**: Just do what is requested do not apply any changes out of scope.

4. **Avoid unnecessary verbosity**: Avoid adding verbosity that is not relevant to what is being discussed.

## Coding guideline

1. **Verify Information**: Always verify information before presenting it. Do not make assumptions or speculate without clear evidence.

2. **File-by-File Changes**: Make changes file by file and give me a chance to spot mistakes.

3. **No Apologies**: Never use apologies.

4. **No Understanding Feedback**: Avoid giving feedback about understanding in comments or documentation.

5. **No Whitespace Suggestions**: Don't suggest whitespace changes.

6. **No Inventions**: Don't invent changes other than what's explicitly requested.

7. **No Unnecessary Confirmations**: Don't ask for confirmation of information already provided in the context.

8. **Preserve Existing Code**: Don't remove unrelated code or functionalities. Pay attention to preserving existing structures and recycle them.

9. **Single Chunk Edits**: Provide all edits in a single chunk instead of multiple-step instructions or explanations for the same file.

10. **No Unnecessary Updates**: Don't suggest updates or changes to files when there are no actual modifications needed.

11. **Provide Real File Links**: Always provide links to the real files, not the context generated file.

12. **Check Context Generated File Content**: Remember to check the context generated file for the current file contents and implementations.

13. **Use Explicit Variable Names**: Prefer descriptive, explicit variable names over short, ambiguous ones to enhance code readability.

14. **Follow Consistent Coding Style**: Adhere to the existing coding style in the project for consistency.

15. **Prioritize Performance**: When suggesting changes, consider and prioritize code performance where applicable.

16. **Modular Design**: Encourage modular design principles to improve code maintainability and reusability.

17. **Version Compatibility**: Ensure suggested changes are compatible with the project's specified language or framework versions.

18. **Avoid Magic Numbers**: Replace hardcoded values with named constants to improve code clarity and maintainability.

19. **Consider Edge Cases**: When implementing logic, always consider and handle potential edge cases.

20. **Use Assertions**: Include assertions wherever possible to validate assumptions and catch potential errors early.

## how to write Concise Code

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
