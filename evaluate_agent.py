from agent import ask, course_crew

# List of expected outcomes
expected_outcomes = [
    {"question":"What is BGP?", "Source Citation":["General Knowledge (External)"],"in_notes":False},
    {"question":"What is IPv4?", "Source Citation":["CN_Logical_IPv4_IPv6_Notes.docx"],"in_notes":True},
]

# Loop each outcome in expected_outcomes
passed_cases = 0
for outcome in expected_outcomes:

    # Ask the question
    user_question = outcome["question"]

    # Generating answer for the question
    answer = ask(user_question)

    # Checking if answer is found in our course notes
    not_mentioned = "Not mentioned in your course notes" in answer
    if outcome["in_notes"]:
        notes_ok = not not_mentioned # not_mentioned == False
    else:
        notes_ok = not_mentioned # not_mentioned == True

    # Checking if source cited are from course notes
    source_general = "General Knowledge (External)" in answer
    if outcome["in_notes"]:
        source_ok = not source_general # source_general == False
    else:
        source_ok = source_general # source_general == True

    # Deciding the pass/fail of the test case
    if notes_ok and source_ok:
        passed_cases += 1
    else:
        print(f"Failed case question is: {outcome['question']}")

print(f"Passed {passed_cases}/{len(expected_outcomes)}")