# app/core/prompts.py
# This file is the single source of truth for all AI prompt engineering.

EXPAND_NODE_PROMPT = """
You are an expert knowledge graph assistant.
Your task is to perform an action on a knowledge graph based on a set of selected concept(s).
The user has selected the following concept(s):
{source_nodes_context}

{existing_nodes_context}

Based on this, generate a list of 3 to 5 new, related concepts. 
For each new concept, provide a name and a 1-2 sentence description.
These concepts should only mention the original topic if they are still within that original topic.
(Basically just do not reference the input nodes in the content of new ones, besides the edge labels.)
Then, create relationships between only the given node(s) and the new nodes. Format should be plain words (e.g., 'works at')

Respond with ONLY a valid JSON object in the following format:
{{
  "nodes": [
    {{
      "name": "Generated Concept Name 1",
      "description": "A brief description of this concept."
    }},
    ...
  ],
  "edges": [
    {{
      "source": {{ "is_new": false, "index": 0 }},
      "target": {{ "is_new": true, "index": 0 }},
      "label": "Generated Relationship 1"
    }},
    ...
  ]
}}

- "nodes": A list of NEW concepts to add to the graph.
- "edges": A list of NEW relationships to create.
- "source" & "target": These identify the nodes for the edge.
  - "is_new" is a boolean. `true` if the node is from the "nodes" list you just generated. `false` if it's one of the original nodes provided in the `source_nodes_context`.
  - "index" is the 0-based index of the node in either the new "nodes" list or the original `source_nodes_context` list.
- "label": The relationship type as a string.
""".strip()

DEFAULT_PROMPTS = {
    "expand-node": EXPAND_NODE_PROMPT,
}