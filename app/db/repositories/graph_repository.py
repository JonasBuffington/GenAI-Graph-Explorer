# app/db/repositories/graph_repository.py
from uuid import UUID
from neo4j import AsyncDriver
from app.models.graph import Node, Edge, Graph, RelationshipType, NodeUpdate
from app.core.exceptions import NodeNotFoundException

class GraphRepository:
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    async def get_graph_for_user(self, user_id: str) -> Graph:
        query = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(n:Concept)
        WITH collect(n) as user_nodes
        UNWIND user_nodes as source_node
        OPTIONAL MATCH (source_node)-[r]->(target_node)
        WHERE target_node IN user_nodes
        RETURN user_nodes as nodes, collect(DISTINCT r) as relationships
        """
        async with self.driver.session() as session:
            result = await session.run(query, {"user_id": user_id})
            record = await result.single()

            if not record or not record["nodes"]:
                return Graph(nodes=[], edges=[])

            nodes_data = record["nodes"]
            rels_data = record["relationships"]

            nodes = [Node.model_validate(node_props) for node_props in nodes_data]

            edges = []
            for rel in rels_data:
                if rel is None:
                    continue
                start_node_id = rel.start_node["id"]
                end_node_id = rel.end_node["id"]
                edges.append(
                    Edge(
                        source_id=start_node_id,
                        target_id=end_node_id,
                        label=RelationshipType(rel.type)
                    )
                )

            return Graph(nodes=nodes, edges=edges)

    async def add_edge_for_user(self, user_id: str, edge: Edge) -> Edge:
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (a:Concept {id: $source_id})
        MATCH (b:Concept {id: $target_id})
        WHERE (u)-[:OWNS]->(a) AND (u)-[:OWNS]->(b)
        CALL apoc.create.relationship(a, $rel_type, {}, b) YIELD rel
        RETURN type(rel) as label
        """
        async with self.driver.session() as session:
            result = await session.run(query, {
                "source_id": str(edge.source_id),
                "target_id": str(edge.target_id),
                "user_id": user_id,
                "rel_type": edge.label.value
            })
            if await result.single() is None:
                raise NodeNotFoundException()
            return edge

    async def update_node(self, node_id: UUID, node_update: NodeUpdate) -> Node | None:
        props_to_update = node_update.model_dump(exclude_unset=True)

        if "mastery_status" in props_to_update and props_to_update["mastery_status"]:
            props_to_update["mastery_status"] = props_to_update["mastery_status"].value

        if not props_to_update:
            # CORRECTNESS: If there's nothing to update, return the current node state.
            # This prevents incorrect 404 errors for empty update payloads.
            return await self.get_node_by_id(node_id)

        query = """
        MATCH (n:Concept {id: $node_id})
        SET n += $props
        RETURN n
        """
        async with self.driver.session() as session:
            result = await session.run(query, {"node_id": str(node_id), "props": props_to_update})
            record = await result.single()
            return Node.model_validate(record["n"]) if record else None

    async def add_node_for_user(self, user_id: str, node: Node) -> Node:
        query = """
        MERGE (u:User {id: $user_id})
        MERGE (n:Concept {id: $node_id})
        ON CREATE SET
            n.name = $name,
            n.description = $description,
            n.mastery_status = $mastery_status,
            n.galaxies = $galaxies,
            n.embedding = $embedding
        MERGE (u)-[:OWNS]->(n)
        RETURN n
        """
        async with self.driver.session() as session:
            result = await session.run(query, {
                "user_id": user_id,
                "node_id": str(node.id),
                "name": node.name,
                "description": node.description,
                "mastery_status": node.mastery_status.value,
                "galaxies": node.galaxies,
                "embedding": node.embedding,
            })
            record = await result.single()
            return Node.model_validate(record["n"])
    
    async def get_node_by_id(self, node_id: UUID) -> Node | None:
        query = "MATCH (n:Concept {id: $node_id}) RETURN n"
        async with self.driver.session() as session:
            result = await session.run(query, {"node_id": str(node_id)})
            record = await result.single()
            return Node.model_validate(record["n"]) if record else None

    async def delete_node_by_id(self, node_id: UUID) -> bool:
        query = "MATCH (n:Concept {id: $node_id}) DETACH DELETE n"
        async with self.driver.session() as session:
            summary = await session.run(query, {"node_id": str(node_id)})
            return summary.summary().counters.nodes_deleted > 0

    async def delete_edge_for_user(self, user_id: str, edge: Edge) -> bool:
        query = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(a:Concept {id: $source_id})
        MATCH (u)-[:OWNS]->(b:Concept {id: $target_id})
        CALL apoc.cypher.do_it(
            'MATCH (a)-[r:' + $rel_type + ']->(b) DELETE r RETURN count(r) as deleted_count',
            {a: a, b: b}
        ) YIELD value
        RETURN value.deleted_count > 0 as was_deleted
        """
        async with self.driver.session() as session:
            result = await session.run(query, {
                "user_id": user_id,
                "source_id": str(edge.source_id),
                "target_id": str(edge.target_id),
                "rel_type": edge.label.value
            })
            record = await result.single()
            # CORRECTNESS: Check the boolean result from the query.
            return record["was_deleted"] if record else False
    
    async def get_galaxies_for_user(self, user_id: str) -> list[str]:
        query = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(n:Concept)
        UNWIND n.galaxies as galaxy_name
        RETURN collect(DISTINCT galaxy_name) as galaxies
        """
        async with self.driver.session() as session:
            result = await session.run(query, {"user_id": user_id})
            record = await result.single()
            return record["galaxies"] if record and record["galaxies"] else []

    async def get_galaxy_graph_for_user(self, user_id: str, galaxy_name: str) -> Graph:
        query = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(n:Concept)
        WHERE $galaxy_name IN n.galaxies
        WITH collect(n) as galaxy_nodes
        UNWIND galaxy_nodes as source_node
        OPTIONAL MATCH (source_node)-[r]->(target_node)
        WHERE target_node IN galaxy_nodes
        RETURN galaxy_nodes as nodes, collect(DISTINCT r) as relationships
        """
        async with self.driver.session() as session:
            result = await session.run(query, {"user_id": user_id, "galaxy_name": galaxy_name})
            record = await result.single()

            if not record or not record["nodes"]:
                return Graph(nodes=[], edges=[])

            nodes_data = record["nodes"]
            rels_data = record["relationships"]

            nodes = [Node.model_validate(node_props) for node_props in nodes_data]

            edges = []
            for rel in rels_data:
                if rel is None:
                    continue
                start_node_id = rel.start_node["id"]
                end_node_id = rel.end_node["id"]
                edges.append(
                    Edge(
                        source_id=start_node_id,
                        target_id=end_node_id,
                        label=RelationshipType(rel.type)
                    )
                )
            return Graph(nodes=nodes, edges=edges)

    async def get_1_hop_neighbors(self, node_id: UUID) -> list[Node]:
        query = """
        MATCH (source:Concept {id: $node_id})--(neighbor:Concept)
        RETURN DISTINCT neighbor
        """
        async with self.driver.session() as session:
            result = await session.run(query, {"node_id": str(node_id)})
            records = [record async for record in result]
            return [Node.model_validate(record["neighbor"]) for record in records]

    async def find_semantically_similar_nodes(
        self,
        query_vector: list[float],
        excluded_node_ids: list[UUID],
        threshold: float,
        limit: int
    ) -> list[Node]:
        excluded_ids_str = [str(uuid) for uuid in excluded_node_ids]
        query = """
            CALL db.index.vector.queryNodes('concept_embeddings', $limit, $query_vector)
            YIELD node, score
            WHERE score >= $threshold AND NOT node.id IN $excluded_ids
            RETURN node
        """
        async with self.driver.session() as session:
            result = await session.run(query, {
                "limit": limit,
                "query_vector": query_vector,
                "threshold": threshold,
                "excluded_ids": excluded_ids_str
            })
            records = [record async for record in result]
            return [Node.model_validate(record["node"]) for record in records]