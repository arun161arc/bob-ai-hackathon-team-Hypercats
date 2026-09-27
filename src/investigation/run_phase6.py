from src.investigation.connection_explainer import explain_connection


queries = [
    ("+919900000101", "+919900000201"),
    ("+919900000101", "356789012345601"),
]


print()
print("CHANAKYA-GRAPH — PHASE 6")
print("EVIDENCE-LINKED CONNECTION EXPLAINER")
print("====================================")


for source, target in queries:

    print()
    print(f"QUERY: Explain why {source} -> {target}")

    try:
        results = explain_connection(source, target)

        for result in results:

            print()
            print("SOURCE       :", result["source_label"])
            print("TARGET       :", result["target_label"])
            print("RELATIONSHIP :", result["relationship"])
            print("EVIDENCE ID  :", result["evidence_id"])
            print("TIMESTAMP    :", result["timestamp"])
            print("STATUS       :", result["evidence_status"])

            if result.get("amount_inr") is not None:
                print("AMOUNT       :", result["amount_inr"])

            print("EXPLANATION  :", result["human_explanation"])

    except Exception as error:

        print()
        print("ERROR:")
        print(error)


print()
print("=" * 70)
print("PHASE 6 COMPLETE")