import litellm
import time
from agent import ask, course_agent

# List of expected outcomes
expected_outcomes = [
    {"question":"In a DNS lookup, in what order are the servers queried, and which one finally supplies the answer?",
     "Source Citation":["dns_lookup_sequence.png"],
      "in_notes":True},
]

passed_cases = 0
tested_cases = 0

# Loop through each individual question
for outcome in expected_outcomes:
    user_question = outcome["question"]
    
    # Retry logic handles JUST this specific question
    retries = 0
    max_tries = 2
    answer = None

    while retries < max_tries:
        try:
            # Generating answer for the question
            answer = ask(user_question)
            break
            
        except litellm.exceptions.RateLimitError as e:
            retries += 1 
            if retries >= max_tries:
                print(f"Maximum tries reached for question: {user_question}")
                raise e
            print("Rate limit hit. Waiting 60 seconds to retry this question...")
            time.sleep(60)

    # If ask(user_question) failed or returned an error phrase, skip evaluation for this question
    if answer is None or "Error couldn't get a response for" in answer:
        print(f"Skipping evaluation for: {user_question} due to agent error.")
        continue # Skip to the next question in expected_outcomes
        
    tested_cases += 1

    # Checking if answer is found in our course notes
    not_mentioned = "Not mentioned in your course notes" in answer
    if outcome["in_notes"]:
        notes_ok = not not_mentioned
    else:
        notes_ok = not_mentioned

    # Checking if source cited are from course notes
    source_general = "General Knowledge (External)" in answer
    if outcome["in_notes"]:
        source_ok = all(source in answer for source in outcome["Source Citation"])
    else:
        source_ok = source_general

    # Deciding the pass/fail of the test case
    if notes_ok and source_ok:
        passed_cases += 1
    else:
        print(f"Failed case question is: {outcome['question']}")

    # Gap of 20 seconds between different questions
    time.sleep(20)

# Final summary printed once at the very end of all questions
print(f"\nFinal Results: Passed {passed_cases}/{tested_cases}")