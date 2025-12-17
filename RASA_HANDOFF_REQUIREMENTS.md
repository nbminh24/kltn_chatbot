# 🤖 Rasa Chatbot Implementation Requirements - Human Handoff Feature

## 📋 Overview
Integrate human handoff capability into the Rasa chatbot, allowing seamless transition from bot to human agent when customers need additional support.

---

## 🎯 Implementation Goals

1. **Detect handoff intent** from customer messages
2. **Trigger backend API** to request human agent
3. **Pause bot conversation** to prevent interference
4. **Resume bot conversation** after human closes the conversation

---

## 📝 Required Changes

### **1. NLU Training Data**

**File:** `data/nlu.yml`

Add new intent for handoff requests:

```yaml
version: "3.1"

nlu:
  - intent: request_human
    examples: |
      - I need to talk to a human
      - Can I speak with a person?
      - I want to talk to an agent
      - Connect me to customer support
      - I need human help
      - Talk to admin
      - I want to speak with someone
      - Get me a human agent
      - This bot isn't helping
      - I need real support
      - Connect me to a real person
      - tôi cần gặp admin
      - tôi muốn nói chuyện với người thật
      - kết nối với nhân viên hỗ trợ
      - bot không giúp được tôi
      - tôi cần hỗ trợ trực tiếp
      - cho tôi nói chuyện với người
```

**Best Practice:** Add at least 15-20 diverse examples per language.

---

### **2. Domain Configuration**

**File:** `domain.yml`

Add intent, action, and responses:

```yaml
version: "3.1"

intents:
  # ... existing intents
  - request_human

actions:
  # ... existing actions
  - action_request_human

responses:
  utter_request_human_initiated:
    - text: "I'm connecting you with one of our human support agents. Please wait a moment..."
  
  utter_request_human_outside_hours:
    - text: "I've forwarded your request to our support team. Our agents are available from 8:00 AM to 8:00 PM. They will respond during working hours."
  
  utter_request_human_error:
    - text: "Sorry, I couldn't connect you to a human agent at this time. Please try again or contact us via email."
```

---

### **3. Stories / Rules**

**File:** `data/rules.yml`

Create rule for immediate handoff:

```yaml
version: "3.1"

rules:
  # ... existing rules
  
  - rule: Request human handoff immediately
    steps:
      - intent: request_human
      - action: action_request_human
```

**Alternative - Story-based approach:**

**File:** `data/stories.yml`

```yaml
version: "3.1"

stories:
  # ... existing stories
  
  - story: customer requests human support
    steps:
      - intent: request_human
      - action: action_request_human
```

---

### **4. Custom Action Implementation**

**File:** `actions/actions.py`

Implement the handoff action:

```python
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import ConversationPaused, FollowupAction
import requests
import logging

logger = logging.getLogger(__name__)

# Backend configuration
BACKEND_URL = "http://localhost:3000/api/v1"  # ⚠️ Update with your backend URL
BACKEND_API_KEY = "your_api_key_here"  # Optional: if you use API key auth


class ActionRequestHuman(Action):
    """
    Custom action to request human handoff.
    
    Flow:
    1. Extract session_id from tracker
    2. Call backend handoff API
    3. Send confirmation message to customer
    4. Pause bot conversation
    """
    
    def name(self) -> Text:
        return "action_request_human"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        # Extract session_id from sender_id or metadata
        session_id = self._extract_session_id(tracker)
        
        if not session_id:
            logger.error("❌ No session_id found in tracker")
            dispatcher.utter_message(response="utter_request_human_error")
            return []
        
        # Call backend handoff API
        success = self._request_handoff(session_id, tracker)
        
        if success:
            logger.info(f"✅ Handoff request successful for session {session_id}")
            
            # Send confirmation message (backend already sends one, but this is immediate)
            dispatcher.utter_message(
                text="I'm inviting one of our human support agents to assist you. "
                     "They will respond shortly. This conversation will now be handled by a human agent."
            )
            
            # ❗ CRITICAL: Pause bot to prevent interference
            return [ConversationPaused()]
        else:
            logger.error(f"❌ Handoff request failed for session {session_id}")
            dispatcher.utter_message(response="utter_request_human_error")
            return []
    
    def _extract_session_id(self, tracker: Tracker) -> int:
        """
        Extract session_id from tracker metadata or sender_id.
        
        Assumes backend sends session_id in metadata when calling Rasa webhook.
        """
        # Method 1: From metadata (recommended)
        metadata = tracker.latest_message.get("metadata", {})
        session_id = metadata.get("session_id")
        
        if session_id:
            return int(session_id)
        
        # Method 2: Parse from sender_id (fallback)
        # If sender_id format is "session_123" or "customer_456"
        sender_id = tracker.sender_id
        
        if sender_id and "_" in sender_id:
            try:
                # Try to extract numeric part
                numeric_part = sender_id.split("_")[-1]
                return int(numeric_part)
            except (ValueError, IndexError):
                pass
        
        # Method 3: Query backend for active session (least efficient)
        customer_id = metadata.get("customer_id")
        if customer_id:
            return self._get_active_session_from_backend(customer_id)
        
        return None
    
    def _request_handoff(self, session_id: int, tracker: Tracker) -> bool:
        """
        Call backend API to request human handoff.
        
        Returns True if successful, False otherwise.
        """
        url = f"{BACKEND_URL}/chat/handoff"
        
        payload = {
            "session_id": session_id,
            "reason": "customer_request"
        }
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Optional: Add API key if backend requires it
        if BACKEND_API_KEY:
            headers["X-API-Key"] = BACKEND_API_KEY
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Backend handoff API success: {response.json()}")
                return True
            else:
                logger.error(f"❌ Backend handoff API error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to call backend handoff API: {e}")
            return False
    
    def _get_active_session_from_backend(self, customer_id: int) -> int:
        """
        Fallback method to get active session from backend.
        """
        url = f"{BACKEND_URL}/chat/sessions/active?customer_id={customer_id}"
        
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                return data.get("session_id")
        except Exception as e:
            logger.error(f"❌ Failed to get active session: {e}")
        
        return None
```

---

### **5. Configuration Updates**

**File:** `config.yml`

Ensure pipeline can handle handoff intent:

```yaml
language: en  # or vi for Vietnamese

pipeline:
  - name: WhitespaceTokenizer
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: CountVectorsFeaturizer
    analyzer: char_wb
    min_ngram: 1
    max_ngram: 4
  - name: DIETClassifier
    epochs: 100
    constrain_similarities: true
  - name: EntitySynonymMapper
  - name: ResponseSelector
    epochs: 100
    constrain_similarities: true
  - name: FallbackClassifier
    threshold: 0.3
    ambiguity_threshold: 0.1

policies:
  - name: MemoizationPolicy
  - name: RulePolicy
  - name: UnexpecTEDIntentPolicy
    max_history: 5
    epochs: 100
  - name: TEDPolicy
    max_history: 5
    epochs: 100
    constrain_similarities: true
```

---

### **6. Backend Integration Points**

#### **6.1 Send Session ID in Webhook Calls**

**Current Implementation (from checkpoint):**
Backend already sends `session_id` in metadata when calling Rasa webhook:

```typescript
// chat.service.ts - sendMessage() method
const metadata: any = {
    session_id: dto.session_id.toString(),
    customer_id: customerId,
    user_jwt_token: authHeader?.replace('Bearer ', ''),
};

await this.httpService.post(
    `${rasaUrl}/webhooks/rest/webhook`,
    {
        sender: senderId,
        message: dto.message,
        metadata: metadata,  // ✅ Session ID included
    }
);
```

**✅ No changes needed** - Backend already sends session_id correctly.

---

#### **6.2 Handle ConversationPaused Event**

When Rasa returns `ConversationPaused()` event, the conversation stops automatically.

**Backend behavior:**
- Bot stops responding to new messages
- `session.status` changes to `human_pending` or `human_active`
- Rasa webhook calls are skipped (already implemented in backend)

---

### **7. Resume Bot After Human Conversation**

**Option 1: Automatic Resume (Recommended)**

When admin closes conversation, backend sets `status = 'closed'`. Customer can start new bot conversation:

```python
# No special action needed - customer just sends new message
# Backend creates new session with status = 'bot'
```

**Option 2: Explicit Resume Action**

If you want bot to resume in same session:

```python
class ActionResumeBot(Action):
    """Resume bot conversation after human closes."""
    
    def name(self) -> Text:
        return "action_resume_bot"
    
    def run(self, dispatcher, tracker, domain):
        session_id = self._extract_session_id(tracker)
        
        # Call backend to update session status to 'bot'
        url = f"{BACKEND_URL}/chat/sessions/{session_id}/resume"
        requests.post(url)
        
        dispatcher.utter_message(
            text="Thank you for chatting with our support team! "
                 "I'm back to help if you have any other questions."
        )
        
        return []
```

---

## 🧪 Testing

### **1. Test Intent Recognition**

```bash
# Test if intent is recognized
rasa shell nlu

# Input test messages:
> I need to talk to a human
> Can I speak with someone?
> tôi cần gặp admin
```

**Expected Output:**
```json
{
  "intent": {
    "name": "request_human",
    "confidence": 0.95
  }
}
```

---

### **2. Test Custom Action**

```bash
# Start action server
rasa run actions

# In another terminal, test the action
rasa shell --debug

# Type: I want to talk to a human
```

**Expected Behavior:**
1. Bot responds: "I'm inviting one of our human support agents..."
2. Backend receives handoff API call
3. Conversation paused (bot stops responding)

---

### **3. Test Full Flow**

**Scenario: Customer requests human during working hours**

```
Customer: I need help with my order
Bot: Sure! I can help you track your order...

Customer: Actually, I want to talk to a person
Bot: I'm inviting one of our human support agents...
     [ConversationPaused]

Admin: (accepts conversation in dashboard)
Admin: Hi! How can I help you?

Customer: My order hasn't arrived
Admin: Let me check that for you...

Admin: (closes conversation)
Bot: (sends closing message via backend)
```

---

## 🔧 Troubleshooting

### **Issue 1: Intent not recognized**
**Solution:** Add more training examples in `nlu.yml` and retrain:
```bash
rasa train nlu
```

### **Issue 2: Backend API call fails**
**Solution:** 
- Check `BACKEND_URL` in `actions.py`
- Verify backend is running
- Check network connectivity
- Review backend logs for errors

### **Issue 3: Bot continues responding after handoff**
**Solution:** 
- Verify `ConversationPaused()` event is returned
- Check backend skip logic in `chat.service.ts` line 209-237
- Ensure session status is updated correctly

### **Issue 4: Session ID not found**
**Solution:**
- Verify backend sends `session_id` in metadata
- Check Rasa tracker: `tracker.latest_message.get("metadata")`
- Add logging to debug session extraction

---

## 📋 Deployment Checklist

**Before Production:**
- [ ] Train model with handoff intent
- [ ] Test intent recognition with 100+ examples
- [ ] Configure correct `BACKEND_URL` in actions.py
- [ ] Test handoff in staging environment
- [ ] Verify bot pauses correctly
- [ ] Test admin conversation flow
- [ ] Test conversation resume
- [ ] Load test with multiple simultaneous handoffs
- [ ] Monitor action server logs
- [ ] Set up error alerting

---

## 🚀 Training Commands

```bash
# Train new model with handoff feature
rasa train

# Validate stories and rules
rasa data validate

# Test NLU
rasa test nlu

# Run action server
rasa run actions

# Run Rasa server
rasa run --enable-api --cors "*"
```

---

## 📊 Monitoring

**Key Metrics to Track:**
1. Handoff request frequency
2. Intent recognition confidence
3. Backend API success rate
4. Average time to admin response
5. Customer satisfaction after human chat

**Logging:**
```python
# Add to actions.py
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Log important events
logger.info(f"🔔 Handoff requested for session {session_id}")
logger.error(f"❌ Backend API failed: {error}")
```

---

## 🔄 Alternative: Contextual Handoff

**Advanced Feature:** Trigger handoff based on conversation context

```python
class ActionSmartHandoff(Action):
    """
    Automatically suggest handoff when:
    - Customer is frustrated (negative sentiment)
    - Bot confidence is low (< 0.5)
    - Complex order issues detected
    """
    
    def name(self) -> Text:
        return "action_smart_handoff"
    
    def run(self, dispatcher, tracker, domain):
        # Analyze conversation context
        last_intent_confidence = tracker.latest_message.get("intent", {}).get("confidence", 1.0)
        
        if last_intent_confidence < 0.5:
            dispatcher.utter_message(
                text="I'm having trouble understanding. Would you like to speak with a human agent?",
                buttons=[
                    {"title": "Yes, connect me", "payload": "/request_human"},
                    {"title": "No, I'll try again", "payload": "/deny"}
                ]
            )
        
        return []
```

---

## 📚 API Integration Summary

| Action | Backend Endpoint | Method |
|--------|-----------------|--------|
| Request handoff | `/chat/handoff` | POST |
| Get active session | `/chat/sessions/active` | GET |
| Check session status | `/chat/history?session_id=X` | GET |

---

**✅ Backend sẵn sàng. Implement Rasa theo tài liệu này!**
**🔥 Nhớ train lại model sau khi thêm intent: `rasa train`**
