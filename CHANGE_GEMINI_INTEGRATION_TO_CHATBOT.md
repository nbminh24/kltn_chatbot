# 🔄 ARCHITECTURAL CHANGE - Gemini AI Integration

**Date:** December 9, 2025  
**Reporter:** Backend Team  
**Type:** Architecture Change / Enhancement Request  
**Priority:** 🟡 MEDIUM  
**Status:** PENDING IMPLEMENTATION

---

## 📋 SUMMARY

Chuyển Gemini AI integration từ **Backend** sang **Chatbot** để đảm bảo tính khoa học và kiến trúc tốt hơn.

**Current state:** Backend có `/api/chatbot/gemini/ask` endpoint xử lý open-ended queries  
**Target state:** Chatbot tự handle Gemini calls, backend chỉ cung cấp business APIs

---

## 🎯 RATIONALE (Lý do thay đổi)

### **Why Move to Chatbot?**

#### **1. Better Architecture** ✅
```
Current (Bad):
User → Chatbot → Backend → Gemini API → Backend → Chatbot → User
     ❌ Unnecessary backend hop

Proposed (Good):
User → Chatbot → Gemini API → Chatbot → User
     ✅ Direct call, faster response
```

#### **2. Scientific Rigor** ✅
- Chatbot là AI conversation layer → Nên tự quản lý AI/LLM calls
- Backend là business logic layer → Chỉ handle database & business rules
- Separation of concerns rõ ràng

#### **3. Performance** ✅
- Reduce latency (bỏ 1 hop qua backend)
- Chatbot control timeout & retry logic
- Parallel calls possible (product search + Gemini)

#### **4. Flexibility** ✅
- Chatbot có thể switch giữa Gemini, GPT, Claude dễ dàng
- A/B testing different models
- Custom prompt engineering trong chatbot code

#### **5. Context Management** ✅
- Chatbot có full conversation context
- Gemini có thể access previous messages
- Better multi-turn conversations

---

## 🔑 GEMINI API CREDENTIALS

### **API Key:**
```
AIzaSyDpca8OMZ6rH2bfoGW-yAji66x2qZyEnGQ
```

**⚠️ Important:** Keep this key secure, don't commit to Git!

---

### **Recommended Model:**

```python
MODEL_NAME = "gemini-1.5-flash"
# or
MODEL_NAME = "gemini-1.5-pro"  # More capable but slower
```

**Model Comparison:**

| Model | Speed | Quality | Cost | Use Case |
|-------|-------|---------|------|----------|
| `gemini-1.5-flash` | ⚡ Fast | ⭐⭐⭐ Good | 💰 Cheap | General chat, quick responses |
| `gemini-1.5-pro` | 🐢 Slower | ⭐⭐⭐⭐⭐ Excellent | 💰💰 Expensive | Complex queries, detailed answers |

**Recommendation:** Start with `gemini-1.5-flash` for production.

---

## 📡 GEMINI API DOCUMENTATION

### **Installation:**

```bash
pip install google-generativeai
```

### **Basic Usage:**

```python
import google.generativeai as genai

# Configure API
genai.configure(api_key="AIzaSyDpca8OMZ6rH2bfoGW-yAji66x2qZyEnGQ")

# Initialize model
model = genai.GenerativeModel('gemini-1.5-flash')

# Generate response
response = model.generate_content("What is the weather like today?")
print(response.text)
```

---

## 🛠️ IMPLEMENTATION GUIDE

### **Step 1: Install Package**

```bash
cd /path/to/chatbot
pip install google-generativeai
```

### **Step 2: Create Gemini Client**

**File:** `actions/gemini_client.py`

```python
import google.generativeai as genai
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Google Gemini AI client for open-ended conversations
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google Gemini API key
            model_name: Model to use (gemini-1.5-flash or gemini-1.5-pro)
        """
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            self.model_name = model_name
            logger.info(f"✅ Gemini client initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            raise
    
    def generate_response(
        self, 
        query: str, 
        context: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Generate response for user query
        
        Args:
            query: User question/message
            context: Optional conversation context
            max_tokens: Max response length
            temperature: Creativity (0.0-1.0)
        
        Returns:
            str: AI response
        """
        try:
            # Build prompt with context
            if context:
                prompt = f"""Context: {context}

User question: {query}

Please provide a helpful, friendly response."""
            else:
                prompt = query
            
            logger.info(f"🤖 Generating Gemini response for: '{query[:50]}...'")
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            
            # Generate
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if response and response.text:
                logger.info(f"✅ Gemini responded ({len(response.text)} chars)")
                return response.text
            else:
                logger.warning("⚠️ Gemini returned empty response")
                return "I'm sorry, I couldn't generate a response. Could you rephrase your question?"
                
        except Exception as e:
            logger.error(f"❌ Gemini error: {str(e)}")
            return "I'm experiencing technical difficulties. Please try again later."
    
    def generate_with_chat_history(
        self, 
        messages: list,
        max_tokens: int = 500
    ) -> str:
        """
        Generate response with full chat history
        
        Args:
            messages: List of {'role': 'user/model', 'content': '...'}
            max_tokens: Max response length
        
        Returns:
            str: AI response
        """
        try:
            # Start chat session
            chat = self.model.start_chat(history=[])
            
            # Add history
            for msg in messages[:-1]:  # All except last
                if msg['role'] == 'user':
                    chat.send_message(msg['content'])
            
            # Send current message
            current_msg = messages[-1]['content']
            response = chat.send_message(current_msg)
            
            return response.text
            
        except Exception as e:
            logger.error(f"❌ Chat history error: {str(e)}")
            return self.generate_response(messages[-1]['content'])
```

---

### **Step 3: Add to Environment Config**

**File:** `.env` or `config.yml`

```env
# Gemini AI Configuration
GEMINI_API_KEY=AIzaSyDpca8OMZ6rH2bfoGW-yAji66x2qZyEnGQ
GEMINI_MODEL=gemini-1.5-flash
```

---

### **Step 4: Create Rasa Action**

**File:** `actions/actions.py`

```python
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from .gemini_client import GeminiClient
import os

class ActionAskGemini(Action):
    """
    Handle open-ended queries using Gemini AI
    """
    
    def __init__(self):
        super().__init__()
        # Initialize Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.gemini = GeminiClient(api_key=api_key, model_name=model)
    
    def name(self) -> Text:
        return "action_ask_gemini"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Get user query
        user_message = tracker.latest_message.get('text', '')
        
        if not user_message:
            dispatcher.utter_message(
                text="I didn't catch that. Could you please repeat?"
            )
            return []
        
        # Optional: Add e-commerce context
        context = """You are a helpful fashion e-commerce assistant. 
        You help customers with product recommendations, style advice, 
        sizing questions, and general fashion inquiries."""
        
        # Generate response
        response = self.gemini.generate_response(
            query=user_message,
            context=context,
            max_tokens=300,
            temperature=0.7
        )
        
        # Send to user
        dispatcher.utter_message(text=response)
        
        return []


class ActionAskGeminiWithHistory(Action):
    """
    Handle open-ended queries with conversation history
    """
    
    def __init__(self):
        super().__init__()
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.gemini = GeminiClient(api_key=api_key, model_name=model)
    
    def name(self) -> Text:
        return "action_ask_gemini_with_history"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Build conversation history
        messages = []
        
        # Get last N events
        for event in tracker.events[-10:]:  # Last 10 messages
            if event.get('event') == 'user':
                messages.append({
                    'role': 'user',
                    'content': event.get('text', '')
                })
            elif event.get('event') == 'bot':
                messages.append({
                    'role': 'model',
                    'content': event.get('text', '')
                })
        
        if not messages:
            dispatcher.utter_message(text="No conversation history found.")
            return []
        
        # Generate with history
        response = self.gemini.generate_with_chat_history(
            messages=messages,
            max_tokens=300
        )
        
        dispatcher.utter_message(text=response)
        
        return []
```

---

### **Step 5: Update Domain & Stories**

**File:** `domain.yml`

```yaml
actions:
  - action_ask_gemini
  - action_ask_gemini_with_history

intents:
  - open_ended_query
  - ask_advice
```

**File:** `data/stories.yml`

```yaml
- story: handle open ended query
  steps:
    - intent: open_ended_query
    - action: action_ask_gemini

- story: handle style advice
  steps:
    - intent: ask_advice
    - action: action_ask_gemini_with_history
```

---

## 🧪 TESTING

### **Test 1: Basic Query**

```python
# Test script
from gemini_client import GeminiClient

client = GeminiClient(
    api_key="AIzaSyDpca8OMZ6rH2bfoGW-yAji66x2qZyEnGQ",
    model_name="gemini-1.5-flash"
)

response = client.generate_response("What colors go well with navy blue?")
print(response)
```

**Expected:** Thoughtful fashion advice about color matching.

---

### **Test 2: With Context**

```python
context = "You are a fashion e-commerce assistant."
response = client.generate_response(
    query="How should I dress for a job interview?",
    context=context
)
print(response)
```

**Expected:** Professional styling advice.

---

### **Test 3: Chat History**

```python
messages = [
    {'role': 'user', 'content': 'I like streetwear style'},
    {'role': 'model', 'content': 'Great! Streetwear is all about comfort and expression.'},
    {'role': 'user', 'content': 'What jacket should I get?'}
]

response = client.generate_with_chat_history(messages)
print(response)
```

**Expected:** Jacket recommendation based on streetwear preference.

---

## 📊 WHEN TO USE GEMINI

### **Use Gemini For:**

✅ Open-ended questions
- "What's trending in fashion?"
- "How do I style a denim jacket?"
- "What's the difference between slim fit and regular fit?"

✅ Style advice
- "What should I wear to a wedding?"
- "How to build a capsule wardrobe?"

✅ General inquiries
- "Tell me about your return policy" (if not in FAQ)
- "Do you ship internationally?"

---

### **DON'T Use Gemini For:**

❌ Product search → Use `action_search_products` + Backend API  
❌ Cart operations → Use Backend API directly  
❌ Order tracking → Use Backend API  
❌ Account management → Use Backend API

---

## 🔒 SECURITY CONSIDERATIONS

### **1. API Key Protection**

```python
# ❌ WRONG - Hardcoded
api_key = "AIzaSyDpca8OMZ6rH2bfoGW-yAji66x2qZyEnGQ"

# ✅ CORRECT - From environment
api_key = os.getenv("GEMINI_API_KEY")
```

### **2. Rate Limiting**

```python
import time
from functools import lru_cache

class GeminiClient:
    def __init__(self):
        self.last_call = 0
        self.min_interval = 0.5  # 500ms between calls
    
    def generate_response(self, query: str):
        # Rate limit
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        # Call API
        response = self.model.generate_content(query)
        self.last_call = time.time()
        
        return response.text
```

### **3. Input Sanitization**

```python
def sanitize_input(text: str) -> str:
    """Remove potentially harmful content"""
    # Remove excessive length
    if len(text) > 1000:
        text = text[:1000]
    
    # Remove special characters if needed
    # text = re.sub(r'[^\w\s,.!?-]', '', text)
    
    return text.strip()

# Usage
safe_query = sanitize_input(user_message)
response = gemini.generate_response(safe_query)
```

---

## 💰 COST ESTIMATION

### **Gemini 1.5 Flash Pricing (as of Dec 2024):**

| Token Type | Cost |
|------------|------|
| Input (prompt) | $0.075 per 1M tokens |
| Output (response) | $0.30 per 1M tokens |

**Example Calculation:**
```
Average query: 50 tokens input + 200 tokens output
Cost per query: (50 × $0.075 + 200 × $0.30) / 1M = $0.000064

1000 queries/day = $0.064/day = $1.92/month
10,000 queries/day = $0.64/day = $19.20/month
```

**Very affordable!** 💰

---

## 📈 MONITORING & LOGGING

### **Add These Logs:**

```python
import logging
import time

logger = logging.getLogger(__name__)

def generate_response(self, query: str) -> str:
    start_time = time.time()
    
    logger.info(f"🤖 Gemini request: query_length={len(query)}")
    
    try:
        response = self.model.generate_content(query)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Gemini response: "
                   f"response_length={len(response.text)}, "
                   f"elapsed={elapsed:.2f}s")
        
        return response.text
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ Gemini error: {str(e)}, elapsed={elapsed:.2f}s")
        raise
```

**Monitor:**
- Request count
- Average response time
- Error rate
- Token usage (if available)

---

## 🎯 SUCCESS CRITERIA

After implementation, verify:

- [ ] Gemini client initializes successfully
- [ ] Can handle open-ended queries
- [ ] Response time < 3 seconds (95th percentile)
- [ ] Responses are relevant and helpful
- [ ] Error handling works (API failures)
- [ ] Logs are clear and informative
- [ ] No API key leaks in logs
- [ ] Rate limiting prevents abuse

---

## 🔄 MIGRATION PLAN

### **Phase 1: Setup (Week 1)**
- [ ] Install `google-generativeai` package
- [ ] Create `GeminiClient` class
- [ ] Add to environment config
- [ ] Unit test Gemini client

### **Phase 2: Integration (Week 1)**
- [ ] Create `action_ask_gemini`
- [ ] Update domain.yml
- [ ] Add stories for open-ended queries
- [ ] Test in Rasa shell

### **Phase 3: Testing (Week 1-2)**
- [ ] Test various query types
- [ ] Verify response quality
- [ ] Load testing
- [ ] Error scenario testing

### **Phase 4: Deployment (Week 2)**
- [ ] Deploy to staging
- [ ] Monitor logs & metrics
- [ ] Gradual rollout to production
- [ ] Update documentation

---

## 📚 RESOURCES

### **Official Documentation:**
- Gemini API: https://ai.google.dev/docs
- Python SDK: https://github.com/google/generative-ai-python

### **Example Prompts for E-commerce:**

```python
SYSTEM_PROMPTS = {
    "fashion_advisor": """You are an expert fashion consultant for an e-commerce store.
    Provide style advice, outfit suggestions, and fashion tips.
    Be friendly, concise, and practical.""",
    
    "product_expert": """You are a product specialist for fashion items.
    Help customers understand materials, sizing, care instructions, and product features.
    Always be accurate and helpful.""",
    
    "general_assistant": """You are a helpful e-commerce assistant.
    Answer questions about fashion, shopping, and style in a friendly manner.
    Keep responses concise (2-3 sentences)."""
}
```

---

## 📞 SUPPORT

### **Questions?**

Contact Backend Team if you need:
- API key regeneration
- Model recommendations
- Integration help
- Performance optimization tips

---

## 🎉 BENEFITS SUMMARY

### **Why This Change is Good:**

1. ✅ **Faster responses** (no backend hop)
2. ✅ **Better architecture** (separation of concerns)
3. ✅ **More flexible** (easy to switch models)
4. ✅ **Full context access** (better conversations)
5. ✅ **Independent scaling** (chatbot & backend separate)
6. ✅ **Scientific approach** (AI layer in AI component)

---

**Status:** ✅ Ready for Implementation  
**Priority:** Medium  
**Timeline:** 1-2 weeks  
**Effort:** ~8-16 hours

**Backend Team Support:** Available for questions & guidance 💪

---

**Document Created:** December 9, 2025  
**Last Updated:** December 9, 2025  
**Version:** 1.0
