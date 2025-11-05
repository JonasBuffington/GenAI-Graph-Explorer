from fastapi import APIRouter, Depends, status, HTTPException, Response
from app.models.graph import Node, Graph, Edge
from app.services.graph_service import GraphService
from app.db.driver import get_db_driver
from neo4j import AsyncDriver
from app.core.exceptions import NodeNotFoundException
from app.core.config import settings

router = APIRouter(
    prefix="/graphs",
    tags=["graphs"]
)

def get_service(driver: AsyncDriver = Depends(get_db_driver)) -> GraphService:
    return GraphService(driver)

@router.get("/{user_id}", response_model=Graph)
async def get_user_graph(
    user_id: str,
    service: GraphService = Depends(get_service)
):
    return await service.get_graph(user_id)

@router.get("/{user_id}/galaxies", response_model=list[str])
async def get_user_galaxies(
    user_id: str,
    service: GraphService = Depends(get_service)
):
    """
    Retrieves a list of all unique galaxy names for a user's graph.
    """
    return await service.get_galaxies(user_id)

@router.get("/{user_id}/galaxies/{galaxy_name}", response_model=Graph)
async def get_galaxy_subgraph(
    user_id: str,
    galaxy_name: str,
    service: GraphService = Depends(get_service)
):
    """
    Retrieves all nodes and edges for a specific galaxy in a user's graph.
    """
    return await service.get_galaxy_graph(user_id, galaxy_name)

@router.post("/{user_id}/nodes", status_code=status.HTTP_201_CREATED, response_model=Node)
async def add_node_to_graph(
    user_id: str,
    node: Node,
    service: GraphService = Depends(get_service)
):
    created_node = await service.create_node(user_id, node)
    return created_node

@router.post("/{user_id}/edges", status_code=status.HTTP_201_CREATED, response_model=Edge)
async def add_edge_to_graph(
    user_id: str,
    edge: Edge,
    service: GraphService = Depends(get_service)
):
    """
    Adds a new edge (relationship) between two nodes in a user's graph.
    Raises 404 if either node does not exist or is not owned by the user.
    """
    try:
        return await service.create_edge(user_id, edge)
    except NodeNotFoundException:
        raise

@router.delete("/{user_id}/edges", status_code=status.HTTP_204_NO_CONTENT)
async def delete_edge_from_graph(
    user_id: str,
    edge: Edge, # FastAPI handles DELETE with body
    service: GraphService = Depends(get_service)
):
    """
    Deletes an edge between two nodes in a user's graph.
    """
    if not await service.delete_edge(user_id, edge):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Edge not found or user does not own nodes")
    return Response(status_code=status.HTTP_204_NO_CONTENT)