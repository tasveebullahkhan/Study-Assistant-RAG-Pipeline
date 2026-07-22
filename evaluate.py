from helpers import build_retriever, DOCX_FILE, PPTX_FILE

# Retriever is here
retriever = build_retriever(DOCX_FILE, PPTX_FILE, 3)

# Eval Metrics
expected_outcomes = [
    {"question":"What is IPv4?", "source":["CN_Logical_IPv4_IPv6_Notes.docx"]},
    {"question":"What is a switch?", "source":["Hub, Switch and Router.pptx"]},
    {"question":"What is IPv6?", "source":["CN_Logical_IPv4_IPv6_Notes.docx"]},
    {"question":"What is Hub?", "source":["Hub, Switch and Router.pptx"]},
    {"question":"How does a router's use of IP addresses relate to logical addressing, and how is that different from how a switch uses MAC addresses?", "source":["Hub, Switch and Router.pptx", "CN_Logical_IPv4_IPv6_Notes.docx"]},  
]

# Taking first expected question source dictionary
passed_cases = 0
for outcome in expected_outcomes:
    test_list = outcome['source']

    # Retriving the top k similar chunks
    result = retriever.invoke(outcome["question"])

    # List of source documents for each chunk
    metadata_source = []
    for doc in result:
        metadata_source.append(doc.metadata['source'])

    # Converting lists to set to check uniqueness not the order
    metadata_source_set = set(metadata_source)
    test_set = set(test_list)

    # Comparing expected source and retrieved source to evaluate correctness
    if (metadata_source_set == test_set):
        passed_cases += 1 
    else:
        print(f"Failed Case qestion(s) is: {outcome['question']}")

print(f"Passed {passed_cases}/{len(expected_outcomes)}")