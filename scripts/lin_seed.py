#!/usr/bin/env python3
"""Seed Linear items via GraphQL API (best-effort)."""

import json
import os
import sys
from urllib import request

API_BASE = "https://api.linear.app/graphql"
TOKEN = os.getenv("LINEAR_TOKEN") or os.environ.get("LINEAR_API_TOKEN")
if not TOKEN:
    print("ERROR: LINEAR_TOKEN (or LINEAR_API_TOKEN) not set.")
    sys.exit(2)

# Load payloads
PAYLOAD_FILE = "linear_import_payload.json"
try:
    with open(PAYLOAD_FILE, "r") as f:
        payloads = json.load(f)
except Exception as e:
    print(f"ERROR loading {PAYLOAD_FILE}: {e}")
    sys.exit(3)

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


def post_graphql(query, variables=None):
    body = {"query": query}
    if variables:
        body["variables"] = variables
    import json as _json

    data = _json.dumps(body).encode("utf-8")
    req = request.Request(API_BASE, data=data, headers=headers)
    with request.urlopen(req) as resp:
        resp_body = resp.read()
        import json as _json

        return _json.loads(resp_body.decode("utf-8"))


def main():
    # Quick sanity check: viewer
    q_viewer = """query { viewer { id name } }"""
    res = post_graphql(q_viewer)
    if "errors" in res:
        print("Viewer check failed:", res["errors"])
    else:
        print("Viewer OK:", res.get("data", {}).get("viewer"))

    created = []
    failed = []

    for item in payloads:
        t = item.get("type")
        if t == "pulse":
            name = item.get("name")
            desc = item.get("description")
            status = item.get("status", "planned").upper()
            due = item.get("due_date")
            # GraphQL mutation (best-effort)
            mutation = """mutation ($input: PulseCreateInput!) { pulseCreate(input: $input) { pulse { id name status dueDate } } }"""
            vars = {"input": {"name": name, "description": desc, "status": status}}
            if due:
                vars["input"]["dueDate"] = due
            if item.get("owner_id"):
                vars["input"]["ownerId"] = item["owner_id"]
            if item.get("related_issues"):
                vars["input"]["relatedIssues"] = item["related_issues"]
            r = post_graphql(mutation, vars)
            if "errors" in r:
                failed.append({"title": name, "error": r["errors"]})
                print("Pulse create failed:", name, r["errors"])
            else:
                pulse = r.get("data", {}).get("pulseCreate", {}).get("pulse", {})
                created.append(
                    {
                        "type": "pulse",
                        "id": pulse.get("id"),
                        "name": pulse.get("name"),
                        "url": None,
                    }
                )
                print("Pulse created:", pulse.get("name"), pulse.get("id"))
        elif t == "customer":
            name = item.get("name")
            contact = item.get("contact_email")
            account = item.get("account_type")
            notes = item.get("notes")
            mutation = """mutation ($input: CustomerCreateInput!) { customerCreate(input: $input) { customer { id name } } }"""
            vars = {"input": {"name": name}}
            if contact:
                vars["input"]["contactEmail"] = contact
            if account:
                vars["input"]["accountType"] = account
            if notes:
                vars["input"]["notes"] = notes
            r = post_graphql(mutation, vars)
            if "errors" in r:
                failed.append({"title": name, "error": r["errors"]})
                print("Customer create failed:", name, r["errors"])
            else:
                customer = (
                    r.get("data", {}).get("customerCreate", {}).get("customer", {})
                )
                created.append(
                    {
                        "type": "customer",
                        "id": customer.get("id"),
                        "name": customer.get("name"),
                    }
                )
                print("Customer created:", customer.get("name"), customer.get("id"))
        elif t == "member":
            name = item.get("name")
            role = item.get("role")
            email = item.get("email")
            joined = item.get("joined_at")
            mutation = """mutation ($input: MemberCreateInput!) { memberCreate(input: $input) { member { id name } } }"""
            vars = {"input": {"name": name}}
            if role:
                vars["input"]["role"] = role
            if email:
                vars["input"]["email"] = email
            if joined:
                vars["input"]["joinedAt"] = joined
            if item.get("status"):
                vars["input"]["status"] = item["status"]
            r = post_graphql(mutation, vars)
            if "errors" in r:
                failed.append({"title": name, "error": r["errors"]})
                print("Member create failed:", name, r["errors"])
            else:
                member = r.get("data", {}).get("memberCreate", {}).get("member", {})
                created.append(
                    {
                        "type": "member",
                        "id": member.get("id"),
                        "name": member.get("name"),
                    }
                )
                print("Member created:", member.get("name"), member.get("id"))
        else:
            print("Unknown type; skipping", item)
            failed.append({"title": item.get("name"), "error": "unknown_type"})

    results = {
        "seeded_at": "now",
        "workspace": None,
        "created_items": created,
        "failed_items": failed,
    }

    with open("lin_seed_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Seed results written to lin_seed_results.json")


if __name__ == "__main__":
    main()
