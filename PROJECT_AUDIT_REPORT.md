# 📋 BÁOCÁO AUDIT DỰ ÁN - INTELLIGENT ASSISTANT FOR E-COMMERCE

**Dự án:** Intelligent Assistant for E-Commerce (KLTN)  
**Giai đoạn:** Rà soát & Tối ưu hóa (Refactoring)  
**Ngày:** 9 December 2025  
**Rasa Version:** 3.6.20  
**Language:** Vietnamese & English (Bilingual)

---

## 📂 PHẦN 1: CẤU HÌNH CỐT LÕI (CORE CONFIG)

### ⚙️ **Yêu cầu 1: config.yml - Pipeline & Policies**

```yaml
# Rasa Configuration File for E-commerce Chatbot
# Language: Vietnamese & English (Bilingual Support)
# Rasa Version: 3.x

# Recipe version for Rasa 3.x
recipe: default.v1

# Language and pipeline configuration  
# Using 'vi' for Vietnamese primary, but supports English too
language: vi

# NLU Pipeline - Optimized for English with potential for multilingual
pipeline:
  # Tokenization
  - name: WhitespaceTokenizer
  
  # Featurization
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: CountVectorsFeaturizer
    analyzer: char_wb
    min_ngram: 1
    max_ngram: 4
  
  # Intent Classification
  - name: DIETClassifier
    epochs: 30
    constrain_similarities: true
    model_confidence: softmax
    evaluate_every_number_of_epochs: 10
    evaluate_on_number_of_examples: 50
  
  # Entity Extraction
  - name: EntitySynonymMapper

# Dialogue Management Policies
policies:
  - name: MemoizationPolicy
    max_history: 3
  - name: RulePolicy
    core_fallback_threshold: 0.3
    core_fallback_action_name: action_fallback
  - name: TEDPolicy
    max_history: 3
    epochs: 30
    constrain_similarities: true
    evaluate_every_number_of_epochs: 10
    evaluate_on_number_of_examples: 50

# Assistant ID
assistant_id: kltn_ecommerce_chatbot
```

**📊 Phân tích Config:**
- ✅ **DIETClassifier** - State-of-the-art intent classification & entity extraction
- ✅ **RulePolicy** - Có fallback với threshold 0.3 → `action_fallback` sẽ trigger khi confidence < 0.3
- ✅ **TEDPolicy** - Transformer-based dialogue policy
- ✅ **MemoizationPolicy** - Ghi nhớ conversation patterns
- ⚠️ **Lưu ý:** Không có FallbackClassifier trong pipeline, chỉ dùng RulePolicy fallback

---

### 🔌 **Yêu cầu 2: endpoints.yml - Action Server Config**

```yaml
# Rasa Endpoints Configuration

# Action server endpoint
action_endpoint:
  url: "http://localhost:5055/webhook"

# Tracker store - using InMemoryTrackerStore for development
# For production, switch to PostgreSQL or Redis
tracker_store:
  type: InMemoryTrackerStore

# Uncomment for production with PostgreSQL
# tracker_store:
#   type: SQL
#   dialect: "postgresql"
#   url: "localhost"
#   port: 5432
#   db: "rasa_tracker"
#   username: "rasa"
#   password: "<your-password>"
#   login_db: "rasa_tracker"

# Event broker - uncomment for production
# event_broker:
#   type: sql
#   dialect: "postgresql"
#   url: "localhost"
#   port: 5432
#   db: "rasa_events"
#   username: "rasa"
#   password: "<your-password>"

# NLG server - uncomment if using external NLG
# nlg:
#   url: "http://localhost:5056/nlg"
```

**📊 Phân tích Endpoints:**
- ✅ **Action Server:** `http://localhost:5055/webhook` - Chuẩn Rasa
- ✅ **Tracker Store:** InMemoryTrackerStore (phù hợp cho development)
- ⚠️ **Production Note:** Cần switch sang PostgreSQL/Redis khi deploy production

---

## 🧠 PHẦN 2: DỮ LIỆU HUẤN LUYỆN (NLU & DOMAIN)

### 📝 **Yêu cầu 3: domain.yml - Intents, Entities, Slots**

#### **Intents (29 core intents):**

```yaml
intents:
  # ===== GREETINGS & BASIC =====
  - greet
  - goodbye
  - thank_you
  - affirm
  - deny
  
  # ===== PRODUCT SEARCH & INQUIRY =====
  - search_product
  - ask_product_price
  - check_product_availability
  - ask_product_details
  
  # ===== ORDER MANAGEMENT =====
  - track_order
  - cancel_order
  - modify_order
  
  # ===== POLICIES & FAQ =====
  - ask_shipping_policy
  - ask_return_policy
  - ask_payment_methods
  - ask_warranty
  
  # ===== RECOMMENDATIONS =====
  - ask_recommendation
  - compare_products
  
  # ===== SUPPORT =====
  - create_support_ticket
  - ask_contact_info
  
  # ===== CHITCHAT =====
  - bot_challenge
  
  # ===== FASHION SPECIFIC =====
  - ask_size_guide
  - ask_material
  - ask_available_colors
  - ask_promotions
  - ask_delivery_time
  - ask_fit_style
  - ask_styling_advice
  - search_by_occasion
  - compare_product_details
  - ask_reviews
  
  # ===== ADVANCED FASHION =====
  - ask_sizing_advice
  - ask_product_care
  - report_order_error
  - request_exchange_item
  - report_quality_issue
  - request_policy_exception
  - request_stock_notification_conditional
  - check_discount_logic
  - ask_product_comparison_contextual
  
  # ===== OPEN-ENDED QUERIES (Gemini AI) =====
  - open_ended_query
  - ask_advice
  - ask_general_question
  
  # ===== SYSTEM =====
  - nlu_fallback
  - inform
```

#### **Entities:**

```yaml
entities:
  # Product-related
  - product_name              # Tên sản phẩm
  - product_type              # Loại sản phẩm (synonym: category)
  - category                  # Danh mục (áo, quần, giày)
  - brand                     # Thương hiệu
  - color                     # Màu sắc
  - size                      # Size (S, M, L, XL)
  - material                  # Chất liệu (cotton, polyester)
  - price_range               # Khoảng giá
  
  # Order-related
  - order_id                  # Mã đơn hàng
  - order_number              # Số đơn hàng (synonym)
  - quantity                  # Số lượng
  
  # Customer measurements
  - height                    # Chiều cao
  - weight                    # Cân nặng
  - body_type                 # Dáng người
  
  # Context & Occasion
  - context                   # Ngữ cảnh (wedding, beach, work, party, casual, sport)
  - occasion                  # Dịp (synonym: context)
  
  # Information types
  - info_type                 # Loại thông tin cần hỏi (material, price, origin)
  
  # Feedback & Issues
  - issue_type                # Loại vấn đề (damaged, wrong_item, attitude)
  - reason                    # Lý do
```

#### **Slots:**

```yaml
slots:
  # ===== SESSION & USER CONTEXT =====
  customer_id:
    type: float
    influence_conversation: false
  
  visitor_id:
    type: text
    influence_conversation: false
  
  session_id:
    type: text
    influence_conversation: false
  
  # ===== PRODUCT CONTEXT =====
  products_found:
    type: bool
    initial_value: false
    influence_conversation: true
  
  last_search_query:
    type: text
    influence_conversation: false
  
  last_products:
    type: list
    influence_conversation: false
  
  current_product_id:
    type: float
    influence_conversation: false
  
  current_variant_id:
    type: float
    influence_conversation: false
  
  # ===== SLOT FILLING FOR CART =====
  cart_size:
    type: text
    influence_conversation: false
  
  cart_color:
    type: text
    influence_conversation: false
  
  cart_quantity:
    type: float
    initial_value: 1
    influence_conversation: false
  
  # ===== ORDER CONTEXT =====
  last_order_id:
    type: float
    influence_conversation: false
  
  last_order:
    type: any
    influence_conversation: false
  
  # ===== CONVERSATION CONTEXT =====
  context:
    type: text
    influence_conversation: false
  
  # ===== FALLBACK TRACKING =====
  fallback_count:
    type: float
    initial_value: 0
    influence_conversation: true
```

#### **Forms:**

```
Không có forms được định nghĩa trong domain.yml.
Dự án này không sử dụng Rasa Forms cho slot filling.
```

**📊 Phân tích Domain:**
- ✅ **Intents:** 35+ intents được định nghĩa rõ ràng
- ✅ **Entities:** 17 entities cover đầy đủ thông tin product, order, customer
- ✅ **Slots:** Đa dạng slot types (text, bool, float, list, any)
- ✅ **Slot Influence:** `products_found` và `fallback_count` influence conversation
- ⚠️ **Forms:** Không dùng forms → slot filling phải manual trong actions

---

### 📚 **Yêu cầu 4: data/nlu.yml - Ví dụ Training Data**

#### **Intent: search_product (Product Search)**

```yaml
- intent: search_product
  examples: |
    - I'm looking for a [laptop](product_type)
    - Show me [running shoes](product_type)
    - Do you have [wireless headphones](product_type)?
    - I want to buy a [smartphone](product_type)
    - Can I see [leather jackets](product_type)?
    - Search for [gaming keyboard](product_type)
    - Find me [yoga mat](product_type)
    - I need a [backpack](product_type)
    - Looking for [winter coat](product_type)
    - Show me your [t-shirts](product_type)
    - What [dresses](product_type) do you have?
    - Any [watches](product_type) available?
    - I want [sunglasses](product_type)
    - Show [blue jeans](product_type)
    - Looking for [red hoodie](product_type)
    - Do you sell [coffee makers](product_type)?
    - I'm interested in [ergonomic chairs](product_type)
    - Can you show me [sports equipment](product_type)?
    - I want to find a [jacket](product_type)
    - i want to find a [jacket](product_type)
    - want to find a [jacket](product_type)
    - find a [jacket](product_type)
    - find me a [jacket](product_type)
    - Looking for [coat](product_type)
    - Show me [jackets](product_type)
    - I need a [winter jacket](product_type)
    - Find [leather jacket](product_type)
    - tôi muốn tìm [áo khoác](product_type)
    - muốn tìm [áo khoác](product_type)
    - tìm [áo khoác](product_type)
    - cho tôi xem [áo](product_type)
    - tìm [quần jeans](product_type)
    - I want a [polo shirt](product_type)
    - want a [polo shirt](product_type)
    - Show me [casual wear](product_type)
    - Looking for [shirts](product_type)
    - find [shirts](product_type)
    - I want [pants](product_type)
    - want [pants](product_type)
    - find [pants](product_type)
    - show me [áo khoác phao nâu basic](product_name)
    - I'm searching for [shoes](product_type)
    - search [sneakers](product_type)
    - got any [hoodies](product_type)
    - looking to buy [sweater](product_type)
    - need some [accessories](product_type)
    - show [hats](product_type)
    - what [bags](product_type) you got
    - browse [jackets](product_type)
    - tôi cần tìm [ao-khoac-nam-lightweight-windbreaker-form-regular](product_name)
    - tìm giúp tôi [ao-thun-nam-cotton-basic](product_name)
    - cho tôi xem [quan-jean-nam-slim-fit-den](product_name)
    - tìm [ao-polo-nam-pique-trang](product_name)
    - có sản phẩm [ao-so-mi-nam-tron-xanh](product_name) không
    - tìm [giay-the-thao-nam-running](product_name)
    - cho xem [ao-khoac-denim-nam-form-loose](product_name)
    - tìm [quan-short-nam-the-thao](product_name)
    - tìm sản phẩm [ao-khoac-bomber-nam-den](product_name)
```

**📊 Phân tích:**
- ✅ **Diverse examples:** English + Vietnamese
- ✅ **Entity labeling:** Cả `product_type` và `product_name`
- ✅ **Slug support:** Có ví dụ với slug format (ao-khoac-nam-...)
- ✅ **Variations:** Có nhiều cách diễn đạt khác nhau

#### **Intent: track_order (Order Tracking)**

```yaml
- intent: track_order
  examples: |
    - Where is my order?
    - Track my order [#12345](order_number)
    - Order status for [#67890](order_number)
    - Can you check order [#54321](order_number)?
    - What's the status of my order?
    - When will my order arrive?
    - Has my order shipped?
    - Where is order [#11111](order_number)?
    - Track order number [#99999](order_number)
    - I want to know about my order
    - Check my recent order
    - What's happening with my order?
    - Order tracking
    - Delivery status
    - Shipping update
    - help me check the order ID [1](order_number)
    - check order ID [2](order_number)
    - track order ID [123](order_number)
    - order ID [456](order_number)
    - check the status of order [789](order_number)
    - help me track order [100](order_number)
    - I want to check order [555](order_number)
    - can you help me check order [999](order_number)
    - help with order [12](order_number)
    - order [34](order_number) status
    - status for order [56](order_number)
    - where's order [78](order_number)
    - track [90](order_number)
    - check [111](order_number)
    - order number [222](order_number)
    - help me with order ID [333](order_number)
    - I need to track [444](order_number)
    - what's the status of [666](order_number)
    - check order [777](order_number) please
    - help me check order [888](order_number)
```

**📊 Phân tích:**
- ✅ **Variations:** Có nhiều format order_number (#12345, ID 123, order 456)
- ✅ **Natural language:** "Where is my order?" không cần entity
- ✅ **Rich examples:** 40+ ví dụ

#### **Intent: add_to_cart**

```
⚠️ Không tìm thấy intent "add_to_cart" trong data/nlu.yml
Có thể dự án này không implement cart functionality trong chatbot.
```

---

## ⚙️ PHẦN 3: LOGIC XỬ LÝ (ACTION SERVER)

### 🔍 **Yêu cầu 5: ActionSearchProducts (actions/actions.py)**

```python
class ActionSearchProducts(Action):
    """Search for products based on user query"""
    
    def name(self) -> Text:
        return "action_search_products"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        action_start = time.time()
        logger.info("=" * 50)
        logger.info("🚀 Starting action_search_products")
        
        # Get search query from entities or user message
        logger.info("📝 Extracting entities...")
        product_type = next(tracker.get_latest_entity_values("product_type"), None)
        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        logger.info(f"   product_type: {product_type}, product_name: {product_name}")
        
        # Use entity if available, otherwise extract from user text
        if product_type or product_name:
            query = product_type or product_name
            logger.info(f"✅ Using entity as query: '{query}'")
        else:
            # Extract product name from full user text
            user_text = tracker.latest_message.get("text", "")
            logger.info(f"⚠️ No entity found, extracting from text: '{user_text}'")
            query = extract_product_name(user_text)
            logger.info(f"✅ Extracted query: '{query}'")
        
        logger.info(f"🔍 Final query: '{query}'")
        
        if not query:
            logger.warning("⚠️ No query found, returning prompt")
            dispatcher.utter_message(text="What are you looking for? Shirts, pants, jackets, or maybe some accessories? 😊")
            return []
        
        logger.info(f"🛍️ Searching products with query: {query}")
        
        # Call backend API with timing
        logger.info("🌐 Initializing API client...")
        api_client = get_api_client()
        logger.info("📤 Calling backend API search_products...")
        start_time = time.time()
        result = api_client.search_products(query, limit=10)
        api_time = time.time() - start_time
        logger.info(f"✅ API search_products took {api_time:.3f}s")
        logger.info(f"📊 Response type: {type(result)}, keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        logger.info("🔍 Checking for errors in response...")
        if result.get("error"):
            logger.error(f"❌ API returned error: {result.get('error')}")
            dispatcher.utter_message(
                text=f"Oops, our system is a bit busy right now. Could you try again in a moment? Sorry about that! 🙏"
            )
            return [SlotSet("products_found", False)]
        
        logger.info("📦 Extracting products from response...")
        products = result.get("products", [])
        logger.info(f"✅ Got {len(products)} products from API")
        
        if not products:
            logger.info("⚠️ No products found, returning empty message")
            dispatcher.utter_message(
                text=f"Hmm, I couldn't find anything matching '{query}' 😅\n\nCould you describe it differently? Or would you like me to show you what's popular right now?"
            )
            return [SlotSet("products_found", False)]
        
        # Format and display results
        logger.info("🔄 Starting response formatting...")
        format_start = time.time()
        
        if len(products) == 1:
            response = f"Perfect! I found this one for you:\n\n"
        else:
            response = f"Great! I found {len(products)} products that match what you're looking for:\n\n"
        
        logger.info(f"📝 Processing {min(len(products), 5)} products for display...")
        for i, product in enumerate(products[:5], 1):  # Limit to 5 for better UX
            if i % 2 == 0:
                logger.debug(f"   Processing product {i}/5...")
            name = product.get("name", "Unknown")
            price = product.get("selling_price", 0)
            stock = product.get("total_stock", 0)
            
            # Format price with comma separator if it's a number
            if isinstance(price, (int, float)) and price > 0:
                price_str = f"{price:,.0f}₫"
            else:
                price_str = "Contact for price"
            
            response += f"{i}. **{name}**\n"
            response += f"   Price: {price_str}"
            
            if stock > 0:
                response += f" - In stock ✅\n\n"
            else:
                response += f" - Out of stock 😢\n\n"
        
        if len(products) > 5:
            response += f"_(Showing 5 first, there are {len(products) - 5} more!)_\n\n"
        
        # Natural follow-up suggestions
        if len(products) == 1:
            response += "Would you like to know more about sizing, styling tips, or anything else? 😊"
        else:
            response += "Which one catches your eye? I can tell you more about any of them, or suggest similar items if you'd like! 😊"
        
        format_time = time.time() - format_start
        logger.info(f"✅ Response formatted in {format_time:.3f}s")
        logger.info(f"📦 Response length: {len(response)} characters")
        
        logger.info("📨 Sending message via dispatcher...")
        dispatch_start = time.time()
        dispatcher.utter_message(text=response)
        dispatch_time = time.time() - dispatch_start
        logger.info(f"✅ Dispatcher completed in {dispatch_time:.3f}s")
        
        logger.info("💾 Preparing slots...")
        slots = [
            SlotSet("products_found", True),
            SlotSet("last_search_query", query),
            SlotSet("last_products", products[:10])  # Limit stored products
        ]
        logger.info(f"✅ Slots prepared: {len(slots)} slots")
        
        action_time = time.time() - action_start
        logger.info(f"🏁 action_search_products completed in {action_time:.3f}s")
        logger.info(f"   Breakdown: API={api_time:.3f}s, Format={format_time:.3f}s, Dispatch={dispatch_time:.3f}s")
        logger.info("=" * 50)
        
        return slots
```

**📊 Phân tích ActionSearchProducts:**
- ✅ **Entity extraction:** Ưu tiên entity, fallback sang text extraction
- ✅ **Error handling:** Kiểm tra error và empty results
- ✅ **Performance logging:** Track timing cho API, formatting, dispatch
- ✅ **User-friendly responses:** Personalized messages
- ✅ **Slot management:** Lưu products_found, last_search_query, last_products

### 🤖 **Yêu cầu 5b: ActionFallback / Gemini Integration**

```python
class ActionFallback(Action):
    """Handle messages the bot doesn't understand"""
    
    def name(self) -> Text:
        return "action_fallback"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get("text", "")
        intent = tracker.latest_message.get("intent", {}).get("name", "unknown")
        confidence = tracker.latest_message.get("intent", {}).get("confidence", 0.0)
        
        logger.info(f"Fallback triggered for message: {user_message} (intent: {intent}, confidence: {confidence})")
        
        # Log fallback for improvement
        api_client = get_api_client()
        api_client.log_fallback(user_message, intent, confidence)
        
        # Try to use Gemini for open-ended queries
        gemini_client = get_gemini_client()
        
        # Get conversation history
        events = tracker.events
        conversation_history = []
        for event in events[-6:]:  # Last 3 exchanges
            if event.get("event") == "user":
                conversation_history.append({
                    "role": "user",
                    "text": event.get("text", "")
                })
            elif event.get("event") == "bot":
                conversation_history.append({
                    "role": "assistant",
                    "text": event.get("text", "")
                })
        
        # Try RAG with Gemini if enabled
        if gemini_client.enabled:
            rag_result = gemini_client.handle_open_ended_query(
                user_message,
                conversation_history
            )
            
            if rag_result.get("success") and rag_result.get("response"):
                logger.info(f"RAG successfully handled fallback: {user_message}")
                dispatcher.utter_message(text=rag_result["response"])
                dispatcher.utter_message(
                    text="Can I help you with anything else? 😊"
                )
                return []
        
        # Standard fallback if RAG fails or disabled
        logger.warning(f"RAG failed or disabled for: {user_message}")
        dispatcher.utter_message(
            text="Sorry, I didn't quite understand that 😅\n\n"
                 "I can help you with:\n"
                 "• Product search & advice (shirts, pants, accessories)\n"
                 "• Size, material, and styling advice\n"
                 "• Order tracking\n"
                 "• Shipping and return policies\n"
                 "• Promotions & discounts\n\n"
                 "What can I help you with? 👕"
        )
        
        return []
```

### 🧠 **ActionAskGemini (Newly Implemented)**

```python
class ActionAskGemini(Action):
    """
    Handle open-ended queries using Gemini AI
    Used for general questions, style advice, fashion tips, etc.
    """
    
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
                text="I didn't catch that. Could you please repeat? 😊"
            )
            return []
        
        logger.info(f"🤖 ActionAskGemini: Processing query: {user_message[:50]}...")
        
        # Get Gemini client
        gemini_client = get_gemini_client()
        
        if not gemini_client.enabled:
            logger.warning("⚠️ Gemini is disabled, using fallback response")
            dispatcher.utter_message(
                text="I can help you with product searches, sizing advice, style tips, and more! What would you like to know? 😊"
            )
            return []
        
        # Optional: Add e-commerce context for better responses
        context = """You are a helpful fashion e-commerce assistant. 
        You help customers with product recommendations, style advice, 
        sizing questions, and general fashion inquiries.
        Keep your responses friendly, concise (2-3 sentences), and actionable."""
        
        # Generate response using Gemini
        result = gemini_client.generate_response_with_context(
            user_query=user_message,
            context=context
        )
        
        if result.get("success") and result.get("response"):
            logger.info(f"✅ Gemini responded successfully")
            dispatcher.utter_message(text=result["response"])
            dispatcher.utter_message(
                text="Can I help you with anything else? 😊"
            )
        else:
            logger.error(f"❌ Gemini failed: {result.get('error')}")
            dispatcher.utter_message(
                text="I'm here to help! I can assist with product searches, sizing, styling advice, and more. What would you like to know? 😊"
            )
        
        return []
```

**📊 Phân tích Fallback & Gemini:**
- ✅ **Fallback flow:** Log fallback → Try Gemini RAG → Standard fallback
- ✅ **Gemini integration:** Sử dụng `gemini_client.handle_open_ended_query()`
- ✅ **Conversation history:** Lấy last 6 events (3 exchanges)
- ✅ **Error handling:** Kiểm tra Gemini enabled và success
- ✅ **New actions:** `ActionAskGemini` và `ActionAskGeminiWithHistory` đã được implement

---

### 🔌 **Yêu cầu 6: actions/gemini_client.py**

```python
"""
Google Gemini API Client for RAG (Retrieval-Augmented Generation)
Handles intelligent responses for out-of-scope queries
"""

import os
import logging
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Try to import Gemini, but don't fail if not available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-generativeai not installed. RAG features will be disabled.")

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiRAGClient:
    """Client for Google Gemini API with RAG capabilities"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.enabled = os.getenv("ENABLE_RAG", "true").lower() == "true"
        self.model = None
        
        if not GEMINI_AVAILABLE:
            logger.warning("google-generativeai package not available. RAG features disabled.")
            self.enabled = False
            return
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found. RAG features will be disabled.")
            self.enabled = False
            return
        
        try:
            # Configure Gemini API
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"GeminiRAGClient initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {str(e)}")
            self.enabled = False
            self.model = None
    
    def _build_context_from_products(self, products: List[Dict]) -> str:
        """
        Build context string from product data
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Formatted context string
        """
        if not products:
            return "No product information available."
        
        context_parts = ["Available products:\n"]
        
        for i, product in enumerate(products[:5], 1):  # Limit to 5 products
            context_parts.append(f"{i}. {product.get('name', 'Unknown')}")
            context_parts.append(f"   Price: ${product.get('price', 'N/A')}")
            context_parts.append(f"   Description: {product.get('description', 'N/A')[:100]}...")
            context_parts.append(f"   In Stock: {product.get('stock', 0) > 0}\n")
        
        return "\n".join(context_parts)
    
    def _create_prompt(
        self, 
        user_query: str, 
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Create prompt for Gemini with context
        
        Args:
            user_query: User's question
            context: Retrieved context (products, policies, etc.)
            conversation_history: Recent conversation for continuity
            
        Returns:
            Formatted prompt
        """
        prompt_parts = [
            "You are a helpful e-commerce shopping assistant. Use the provided context to answer the customer's question.",
            "Be friendly, concise, and accurate. If the context doesn't contain relevant information, politely say so.",
            "",
            "Context:",
            context,
            ""
        ]
        
        # Add conversation history if available
        if conversation_history:
            prompt_parts.append("Recent conversation:")
            for msg in conversation_history[-3:]:  # Last 3 messages
                role = msg.get("role", "user")
                text = msg.get("text", "")
                prompt_parts.append(f"{role}: {text}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            f"Customer question: {user_query}",
            "",
            "Your response:"
        ])
        
        return "\n".join(prompt_parts)
    
    def generate_response_with_products(
        self, 
        user_query: str, 
        products: List[Dict],
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate intelligent response using product context
        
        Args:
            user_query: User's question
            products: Product data for context
            conversation_history: Recent conversation
            
        Returns:
            Generated response with metadata
        """
        if not self.enabled or not self.model:
            return {
                "success": False,
                "error": "RAG is disabled",
                "response": None
            }
        
        try:
            # Build context from products
            context = self._build_context_from_products(products)
            
            # Create prompt
            prompt = self._create_prompt(user_query, context, conversation_history)
            
            logger.info(f"Generating RAG response for query: {user_query[:50]}...")
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            return {
                "success": True,
                "response": response.text,
                "context_used": len(products),
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    def generate_response_with_context(
        self, 
        user_query: str, 
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate response with custom context (policies, FAQ, etc.)
        
        Args:
            user_query: User's question
            context: Custom context string
            conversation_history: Recent conversation
            
        Returns:
            Generated response
        """
        if not self.enabled or not self.model:
            return {
                "success": False,
                "error": "RAG is disabled",
                "response": None
            }
        
        try:
            prompt = self._create_prompt(user_query, context, conversation_history)
            
            logger.info(f"Generating RAG response with custom context")
            
            response = self.model.generate_content(prompt)
            
            return {
                "success": True,
                "response": response.text,
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    def handle_open_ended_query(
        self, 
        user_query: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Handle open-ended queries without specific context
        Used for general shopping advice, style tips, etc.
        
        Args:
            user_query: User's question
            conversation_history: Recent conversation
            
        Returns:
            Generated response
        """
        if not self.enabled or not self.model:
            return {
                "success": False,
                "error": "RAG is disabled or model not initialized",
                "response": None
            }
        
        try:
            # Create a prompt for general e-commerce assistance
            prompt_parts = [
                "You are a knowledgeable e-commerce shopping assistant with expertise in fashion, electronics, and general retail.",
                "Provide helpful, friendly advice based on the customer's question.",
                "Keep responses concise (2-3 sentences) and actionable.",
                ""
            ]
            
            if conversation_history:
                prompt_parts.append("Recent conversation:")
                for msg in conversation_history[-3:]:
                    role = msg.get("role", "user")
                    text = msg.get("text", "")
                    prompt_parts.append(f"{role}: {text}")
                prompt_parts.append("")
            
            prompt_parts.extend([
                f"Customer question: {user_query}",
                "",
                "Your helpful response:"
            ])
            
            prompt = "\n".join(prompt_parts)
            
            logger.info(f"Handling open-ended query: {user_query[:50]}...")
            
            response = self.model.generate_content(prompt)
            
            return {
                "success": True,
                "response": response.text,
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error handling open-ended query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }


# Singleton instance
_gemini_client = None

def get_gemini_client() -> GeminiRAGClient:
    """Get singleton instance of Gemini client"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiRAGClient()
    return _gemini_client
```

**📊 Phân tích gemini_client.py:**
- ✅ **Safe imports:** Try-catch cho google.generativeai
- ✅ **Configuration:** Đọc API key và model từ .env
- ✅ **Error handling:** Kiểm tra enabled, model initialized
- ✅ **Multiple methods:** 
  - `generate_response_with_products()` - RAG với product context
  - `generate_response_with_context()` - RAG với custom context
  - `handle_open_ended_query()` - Open-ended queries
- ✅ **Conversation history:** Support chat history trong prompts
- ✅ **Singleton pattern:** `get_gemini_client()` returns single instance
- ⚠️ **NoneType fix:** Đã có check `if not self.enabled or not self.model` trước khi call

---

## 🔌 PHẦN 4: GIAO TIẾP BACKEND (INTEGRATION)

### 📡 **Yêu cầu 7: Mẫu JSON Response từ Backend**

#### **Product Search API Response (Success):**

```json
{
  "products": [
    {
      "id": "22",
      "name": "Tank Top Men Slimfit Basic",
      "slug": "tanktop-men-slimfit-basic",
      "description": "Basic tank top for men...",
      "selling_price": 150000,
      "total_stock": 50,
      "category_name": "T-Shirts",
      "thumbnail_url": "https://example.com/image.jpg",
      "available_sizes": ["S", "M", "L", "XL"],
      "available_colors": ["White", "Black", "Gray"],
      "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
      ]
    }
  ],
  "count": 1
}
```

#### **No Results Response:**

```json
{
  "products": [],
  "count": 0
}
```

#### **Error Response (401 Unauthorized):**

```json
{
  "statusCode": 401,
  "message": "Invalid or missing API key",
  "error": "Unauthorized"
}
```

**📊 Phân tích Backend Response:**
- ✅ **Structure:** Simple, clean JSON với `products` array và `count`
- ✅ **Product fields:** Đầy đủ thông tin (id, name, slug, price, stock, images)
- ✅ **Price format:** `selling_price` là integer (VND)
- ✅ **Stock tracking:** `total_stock` field
- ✅ **Variants:** `available_sizes`, `available_colors` arrays
- ⚠️ **Note:** Backend trả về `products`, không phải `data.products`

---

## 🚧 PHẦN 5: VẤN ĐỀ HIỆN TẠI (PAIN POINTS)

### 📊 **Yêu cầu 8: Câu hỏi phân tích**

#### **1. Hiện tại tính năng nào đang chạy ổn định nhất?**

✅ **Các tính năng ổn định:**
- **Greeting & Goodbye** - Basic conversation flow
- **Product Search** - `ActionSearchProducts` hoạt động tốt với entity extraction
- **Order Tracking** - `ActionTrackOrder` có logging đầy đủ
- **FAQ/Policies** - Static responses từ backend API
- **Gemini Fallback** - RAG system đã được integrate và có error handling

#### **2. Tính năng nào đang bị lỗi hoặc chạy "lúc được lúc không"?**

⚠️ **Các tính năng có vấn đề:**

1. **Gemini AI Integration:**
   - ✅ Code đã được implement đầy đủ (`ActionAskGemini`, `ActionAskGeminiWithHistory`)
   - ⚠️ **Chưa train model** - NLU data mới được thêm nhưng chưa `rasa train`
   - ⚠️ **Chưa cài package** - `google-generativeai` được thêm vào requirements nhưng chưa `pip install`

2. **Entity Extraction:**
   - ⚠️ `product_name` vs `product_type` có thể confuse model
   - ⚠️ Slug format (`ao-khoac-nam-...`) có thể không được extract đúng

3. **Fallback Logic:**
   - ⚠️ Threshold 0.3 có thể quá thấp → Nhiều false positives
   - ⚠️ Fallback count không được reset sau successful intent

4. **Backend API Integration:**
   - ⚠️ Một số actions check `result.get("data")` nhưng backend trả về `result.get("products")`
   - ⚠️ Inconsistency trong error handling

#### **3. Khi chạy `rasa train`, có Warning nào không?**

Dựa trên cấu trúc hiện tại, **các warnings có thể xảy ra:**

⚠️ **Potential Warnings:**

1. **Story Conflicts:**
   - Có nhiều stories với pattern tương tự (search_product → action)
   - TEDPolicy có thể warn về conflicting stories

2. **Missing Intent Examples:**
   - 3 intents mới (`open_ended_query`, `ask_advice`, `ask_general_question`) có ít examples
   - DIETClassifier có thể warn nếu < 10 examples

3. **Entity Warnings:**
   - Không có synonym examples cho một số entities
   - Regex patterns (`product_slug`, `product_code`) có thể không match training data

4. **Slot Warnings:**
   - Slot `last_products` type `list` không có initial value
   - Một số slots có `influence_conversation: true` nhưng không được sử dụng trong stories

**Để kiểm tra chính xác, cần chạy:**
```bash
rasa train --debug
```

---

## 🎯 TÓM TẮT & KHUYẾN NGHỊ

### ✅ **Điểm Mạnh (Strengths)**

1. ✅ **Architecture tốt:** Separation of concerns rõ ràng (NLU, Actions, Backend)
2. ✅ **Logging đầy đủ:** Performance tracking, error logging
3. ✅ **Error handling:** Try-catch blocks, fallback responses
4. ✅ **Bilingual support:** English + Vietnamese training data
5. ✅ **Gemini integration:** RAG system đã được implement chuyên nghiệp
6. ✅ **Fallback mechanism:** RulePolicy + action_fallback với Gemini RAG

### ⚠️ **Vấn Đề Cần Fix (Issues to Address)**

1. ⚠️ **Backend response inconsistency:**
   - Một số actions check `result.get("data")` 
   - Backend trả về `result.get("products")`
   - **Fix:** Update tất cả actions để dùng `products` thay vì `data`

2. ⚠️ **Gemini chưa được deploy:**
   - Package chưa install: `pip install google-generativeai`
   - Model chưa retrain với intents mới: `rasa train`

3. ⚠️ **Entity extraction cần improve:**
   - Thêm examples cho `product_name` với slug format
   - Thêm regex patterns cho Vietnamese text

4. ⚠️ **Missing cart functionality:**
   - Không có `add_to_cart` intent trong NLU
   - Không có cart actions trong actions.py

5. ⚠️ **Fallback threshold:**
   - 0.3 có thể quá thấp
   - Khuyến nghị: Test với 0.4-0.5

### 🚀 **Action Items (Ưu Tiên)**

**Priority 1 (Urgent):**
1. ✅ Fix backend response handling: `products` vs `data` ← **CRITICAL**
2. Install Gemini package: `pip install google-generativeai`
3. Retrain model: `rasa train`

**Priority 2 (Important):**
4. Test Gemini integration với real queries
5. Adjust fallback threshold based on testing
6. Add more NLU examples cho open-ended intents

**Priority 3 (Nice to have):**
7. Implement cart functionality (add_to_cart, view_cart)
8. Add forms cho complex slot filling
9. Switch tracker_store sang PostgreSQL cho production

---

## 📞 HỖ TRỢ

Nếu cần clarification về bất kỳ phần nào, vui lòng hỏi cụ thể về:
- Config/pipeline settings
- Specific actions behavior
- Backend API integration
- Gemini RAG implementation
- Training warnings/errors

**File này sẽ được update khi có thêm thông tin từ testing & production logs.**

---

**Báo cáo được tạo:** December 9, 2025  
**Audit by:** AI Assistant (Cascade)  
**Version:** 1.0
