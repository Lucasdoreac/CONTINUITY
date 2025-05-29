from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db, get_sessao_by_id # Ensure these are correctly imported
# from .. import models # Not strictly needed for this placeholder but good for future

router = APIRouter(
    tags=["WebSockets"],
)

@router.websocket("/ws/v1/sessions/{session_id}")
async def websocket_session_endpoint(
    websocket: WebSocket, 
    session_id: str, 
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time communication within a session.
    - Verifies session existence.
    - Echoes received messages.
    """
    db_session = get_sessao_by_id(db, session_id=session_id)
    
    if not db_session:
        # It's important to accept the connection before closing it with a specific code.
        # Some clients might not see the close code if the connection isn't accepted first.
        await websocket.accept() 
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session not found")
        print(f"WebSocket connection denied for non-existent session: {session_id}")
        return

    await websocket.accept()
    print(f"WebSocket connection accepted for session: {session_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Message received in session {session_id}: {data}")
            
            # Placeholder: Echo message back to the client
            await websocket.send_text(f"Echo from session {session_id}: {data}")
            
            # Future:
            # - Process incoming data (e.g., CRDT operations, commands).
            # - Store relevant data if needed.
            # - Broadcast updates to other clients in the same session (requires a ConnectionManager).
            
    except WebSocketDisconnect:
        print(f"Client disconnected from session {session_id}")
        # Future: Handle client disconnection, e.g., remove from a connection manager.
    except Exception as e:
        print(f"Error in WebSocket for session {session_id}: {e}")
        # Attempt to close gracefully if an unexpected error occurs.
        # Avoid sending error details to client unless it's a specific design choice.
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
