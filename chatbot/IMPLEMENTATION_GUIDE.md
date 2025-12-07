# 🚀 CHATBOT IMPLEMENTATION GUIDE

**Language:** English (100%)  
**Created:** 2024-12-07

---

## 1. SYSTEM FLOW SUMMARY

### Main Message Flow
```
USER → FRONTEND → BACKEND (save to DB) → RASA (NLU + Dialog) 
     → RASA calls BACKEND APIs (internal) → RASA response 
     → BACKEND (save bot messages) → FRONTEND (render)
```

### Key Points
- **Frontend NEVER calls Rasa directly** - always through Backend proxy
- **Rasa calls Backend** via Internal APIs with `X-Internal-Api-Key` header
- **Session Management:** Guest (visitor_id) vs Logged-in (customer_id)
- **Slot Filling:** Rasa asks for missing info (size, color) before executing actions
- **Support:** Async tickets only, NO real-time chat with admin

---

## 2. BACKEND TASKS

| # | Task | Priority | Estimate | Assignee |
|---|------|----------|----------|----------|
| **2.1 MODULE SETUP** ||||
| 2.1.1 | Create chatbot module structure | HIGH | 2h | Backend |
| 2.1.2 | Implement InternalApiKeyGuard | HIGH | 1h | Backend |
| **2.2 HIGH PRIORITY APIs (MVP)** ||||
| 2.2.1 | POST /api/chatbot/cart/add | HIGH | 3h | Backend |
| 2.2.2 | POST /api/chatbot/orders/:id/cancel | HIGH | 2h | Backend |
| 2.2.3 | GET /api/chatbot/size-chart/:category | HIGH | 2h | Backend |
| **2.3 MEDIUM PRIORITY APIs** ||||
| 2.3.1 | POST /api/chatbot/wishlist/add | MEDIUM | 2h | Backend |
| 2.3.2 | POST /api/chatbot/size-advice | MEDIUM | 3h | Backend |
| 2.3.3 | GET /api/chatbot/products/recommend | MEDIUM | 4h | Backend |
| 2.3.4 | POST /api/chatbot/gemini/ask | LOW | 4h | Backend |
| **2.4 TESTING** ||||
| 2.4.1 | Unit tests for all APIs | HIGH | 4h | Backend |
| 2.4.2 | Integration tests with Rasa | MEDIUM | 3h | Backend |
| **2.5 DOCUMENTATION** ||||
| 2.5.1 | Swagger docs + README | HIGH | 2h | Backend |

**Total Backend Estimate: ~32 hours (~4 days)**

---

## 3. RASA AI TASKS

| # | Task | Priority | Estimate | Assignee |
|---|------|----------|----------|----------|
| **3.1 PROJECT SETUP** ||||
| 3.1.1 | Initialize Rasa project | HIGH | 2h | Rasa |
| 3.1.2 | Configure config.yml, endpoints.yml | HIGH | 1h | Rasa |
| **3.2 NLU TRAINING DATA** ||||
| 3.2.1 | Create 29 intents with examples (nlu.yml) | HIGH | 6h | Rasa |
| 3.2.2 | Define domain.yml (intents, slots, responses) | HIGH | 3h | Rasa |
| **3.3 CUSTOM ACTIONS** ||||
| 3.3.1 | action_search_products | HIGH | 3h | Rasa |
| 3.3.2 | action_add_to_cart (with slot filling) | HIGH | 4h | Rasa |
| 3.3.3 | action_check_stock | HIGH | 2h | Rasa |
| 3.3.4 | action_get_promotions | MEDIUM | 2h | Rasa |
| 3.3.5 | action_add_to_wishlist | MEDIUM | 2h | Rasa |
| 3.3.6 | action_get_size_chart | MEDIUM | 2h | Rasa |
| 3.3.7 | action_size_advice | MEDIUM | 2h | Rasa |
| 3.3.8 | action_get_orders | MEDIUM | 2h | Rasa |
| 3.3.9 | action_cancel_order | MEDIUM | 2h | Rasa |
| 3.3.10 | action_create_ticket | HIGH | 2h | Rasa |
| **3.4 STORIES & RULES** ||||
| 3.4.1 | Create conversation stories | HIGH | 4h | Rasa |
| 3.4.2 | Create rules for slot filling | MEDIUM | 2h | Rasa |
| **3.5 TRAINING & TESTING** ||||
| 3.5.1 | Train initial model | HIGH | 2h | Rasa |
| 3.5.2 | Test core flows (10+ scenarios) | HIGH | 3h | Rasa |

**Total Rasa Estimate: ~46 hours (~6 days)**

---

## 4. FRONTEND TASKS

| # | Task | Priority | Estimate | Assignee |
|---|------|----------|----------|----------|
| **4.1 CHAT WIDGET UI** ||||
| 4.1.1 | Create ChatWidget component structure | HIGH | 6h | Frontend |
| 4.1.2 | Implement message types (text, products, buttons) | HIGH | 4h | Frontend |
| 4.1.3 | Handle custom responses from Rasa | HIGH | 3h | Frontend |
| **4.2 SESSION MANAGEMENT** ||||
| 4.2.1 | Implement guest session (visitor_id) | HIGH | 2h | Frontend |
| 4.2.2 | Implement logged-in session (JWT) | HIGH | 2h | Frontend |
| 4.2.3 | Implement session merge after login | MEDIUM | 3h | Frontend |
| **4.3 INTERACTIONS** ||||
| 4.3.1 | Product carousel with "View Details" | HIGH | 3h | Frontend |
| 4.3.2 | Button groups for size/color selection | HIGH | 2h | Frontend |
| 4.3.3 | Quick actions (Add to Cart from chat) | MEDIUM | 3h | Frontend |
| **4.4 UX POLISH** ||||
| 4.4.1 | Loading states & animations | MEDIUM | 2h | Frontend |
| 4.4.2 | Error handling & retry | MEDIUM | 2h | Frontend |
| 4.4.3 | Mobile responsive design | HIGH | 3h | Frontend |
| **4.5 TESTING** ||||
| 4.5.1 | Component tests | MEDIUM | 3h | Frontend |
| 4.5.2 | E2E tests with real backend | HIGH | 4h | Frontend |

**Total Frontend Estimate: ~42 hours (~5 days)**

---

## 5. INTEGRATION & TESTING

| # | Task | Priority | Estimate | Team |
|---|------|----------|----------|------|
| 5.1 | End-to-end flow testing | HIGH | 4h | All |
| 5.2 | Performance testing (load, response time) | MEDIUM | 3h | Backend |
| 5.3 | Security audit (API keys, auth) | HIGH | 2h | Backend |
| 5.4 | User acceptance testing | HIGH | 4h | PM + QA |
| 5.5 | Bug fixes & polish | MEDIUM | 8h | All |

**Total Integration Estimate: ~21 hours (~3 days)**

---

## 6. TIMELINE & DEPENDENCIES

### Week 1: Foundation (MVP Core)
**Backend:**
- Day 1-2: Module setup + InternalApiKeyGuard
- Day 3-4: Implement 3 HIGH priority APIs (cart, cancel order, size chart)
- Day 5: Unit tests + documentation

**Rasa:**
- Day 1-2: Project setup + NLU data for 15 basic intents
- Day 3-4: Implement 4 core actions (search, add cart, stock, ticket)
- Day 5: Train model + basic testing

**Frontend:**
- Day 1-2: Chat widget structure + message components
- Day 3-4: Session management (guest + logged-in)
- Day 5: Product carousel + button groups

---

### Week 2: Enhancement
**Backend:**
- Day 1-2: 4 MEDIUM priority APIs (wishlist, size advice, recommend, gemini)
- Day 3: Integration tests with Rasa

**Rasa:**
- Day 1-2: Remaining 6 actions (wishlist, size, orders, etc.)
- Day 3-4: Stories + rules + slot filling logic
- Day 5: Model fine-tuning

**Frontend:**
- Day 1-2: Session merge + quick actions
- Day 3-4: UX polish + animations
- Day 5: Component tests

---

### Week 3: Integration & Polish
**All Teams:**
- Day 1-2: End-to-end integration testing
- Day 3: Bug fixes
- Day 4: Performance optimization
- Day 5: UAT + final polish

---

## 7. CRITICAL SUCCESS FACTORS

### Backend
✅ Internal API Key Guard working correctly  
✅ All APIs return standardized format  
✅ Customer/variant validation robust  
✅ Error handling comprehensive  

### Rasa
✅ NLU accuracy >85% for core intents  
✅ Slot filling works smoothly  
✅ Actions call Backend APIs successfully  
✅ Context tracking reliable  

### Frontend
✅ Chat widget responsive on all devices  
✅ Session management works (guest + login + merge)  
✅ Custom message types render correctly  
✅ Error states handled gracefully  

---

## 8. ENVIRONMENT SETUP

### Backend (.env)
```env
INTERNAL_API_KEY=your-super-secret-key-123456
RASA_SERVER_URL=http://localhost:5005
GEMINI_API_KEY=your-gemini-key
SIZE_CHART_SHIRT_URL=https://cdn.site.com/size-shirt.png
SIZE_CHART_PANTS_URL=https://cdn.site.com/size-pants.png
SIZE_CHART_SHOES_URL=https://cdn.site.com/size-shoes.png
```

### Rasa (actions/actions.py)
```python
BACKEND_URL = "http://localhost:3000"
INTERNAL_API_KEY = "your-super-secret-key-123456"
```

---

## 9. TESTING CHECKLIST

### Backend
- [ ] POST /api/chatbot/cart/add returns 200 with valid data
- [ ] POST /api/chatbot/cart/add returns 404 if customer not found
- [ ] POST /api/chatbot/cart/add returns 401 without API key
- [ ] All APIs have unit tests with >80% coverage

### Rasa
- [ ] "Find black t-shirt" → Returns product carousel
- [ ] "Add to cart" → Asks for size → Asks for color → Adds successfully
- [ ] "Where is my order?" → Returns order status
- [ ] "Talk to human" → Creates support ticket

### Frontend
- [ ] Chat widget opens/closes smoothly
- [ ] Guest user creates session automatically
- [ ] Messages appear in correct order
- [ ] Product carousel clickable
- [ ] Button groups work (size/color selection)

### Integration
- [ ] Full flow: Search → View → Add to Cart → Success
- [ ] Session merge works after login
- [ ] Error messages display correctly
- [ ] Performance: Response time <2s for most requests

---

**Total Project Estimate: 141 hours (~3 weeks with 3-person team)**

**Created:** 2024-12-07  
**Status:** Ready for Implementation
