import time
from agent import ask

# List of expected outcomes
expected_outcomes = [
    {"question":"In a DNS lookup, in what order are the servers queried, and which one finally supplies the answer?",
     "Source Citation":["dns_lookup_sequence.png"],
      "in_notes":True},
    {"question":"What is the allowed size range for the payload of an Ethernet frame?",
     "Source Citation":["ethernet_frame_path.png"],
      "in_notes":True},
    {"question":"Which transport protocol uses retransmission and flow control, and which one is described as low overhead?",
     "Source Citation":["tcp_vs_udp.png"],
      "in_notes":True},
      
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

    # Gap of 10 seconds between each iteration
    time.sleep(20)
print(f"Passed {passed_cases}/{tested_cases}")