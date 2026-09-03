from agent import ask

# List of expected outcomes
expected_outcomes = [
    {"question":"What is network layer in computer networks", "Source Citation":["General Knowledge (External)"], "in_notes":False}
]

# Loop each outcome in expected_outcomes
passed_cases = 0
tested_cases = 0
for outcome in expected_outcomes:

    # Ask the question
    user_question = outcome["question"]

    # Generating answer for the question
    answer = ask(user_question)

    # Not running the test case on finding errors
    if "Error couldn't get a response for" in answer:
        break
    tested_cases += 1

    # Checking if answer is found in our course notes
    not_mentioned = "Not mentioned in your course notes" in answer
    if outcome["in_notes"]:
        notes_ok = not not_mentioned # not_mentioned == False
    else:
        notes_ok = not_mentioned # not_mentioned == True

    # Checking if source cited are from course notes
    source_general = "General Knowledge (External)" in answer
    if outcome["in_notes"]:
        source_ok = all(source in answer for source in outcome["Source Citation"])
    else:
        source_ok = source_general # source_general == True

    # Debug lines
    print(f"notes_ok={notes_ok}, source_ok={source_ok}")
    print(answer)

    # Deciding the pass/fail of the test case
    if notes_ok and source_ok:
        passed_cases += 1
    else:
        print(f"Failed case question is: {outcome['question']}")

print(f"Passed {passed_cases}/{tested_cases}")