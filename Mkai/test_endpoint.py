import sys
sys.path.insert(0, 'backend')

import asyncio
from app.core.database import SessionLocal
from app.schemas.chat import ChatRequest
from app.schemas.conversation import ConversationCreate
from app.schemas.message import MessageCreate
from app.services.assistant_service import AssistantService
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService

async def test():
    db = SessionLocal()
    try:
        request = ChatRequest(message="test", conversation_id=None)
        
        # Create conversation
        conv = ConversationService(db).create_conversation(ConversationCreate(title=request.message[:40] or "Yeni konuşma"))
        conversation_id = conv.id
        print(f"Created conversation: {conversation_id}")
        
        # Build history
        messages = MessageService(db).list_messages_for_conversation(conversation_id)
        history = [{"role": m.role, "content": m.content} for m in messages]
        print(f"History: {len(history)} messages")
        
        # Generate reply
        assistant_service = AssistantService()
        response = await assistant_service.generate_reply(request, history=history)
        print(f"Generated reply: {response.reply[:200]}")
        
        # Save messages
        MessageService(db).create_message(MessageCreate(content=request.message, role="user", conversation_id=conversation_id))
        MessageService(db).create_message(MessageCreate(content=response.reply, role="assistant", conversation_id=conversation_id))
        print("Saved messages")
        
    except Exception as e:
        import traceback
        print(f"Error: {type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        db.close()

asyncio.run(test())
