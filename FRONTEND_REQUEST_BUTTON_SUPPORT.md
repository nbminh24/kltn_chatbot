# Frontend Request: Rasa Button Support for Chatbot

**Date:** 12/12/2024  
**Priority:** HIGH  
**Component:** Frontend - Chat Widget  
**Requested by:** Chatbot Team

---

## 📋 Request Summary

Frontend cần hỗ trợ **Rasa buttons** để chatbot có thể hiển thị size/color options dưới dạng buttons thay vì text input. Điều này giúp tránh lỗi matching do user nhập sai format.

---

## 🎯 Use Case

**Current Flow (Text Input - LỖI):**
```
Bot: "What size would you like?"
User types: "xl" hoặc "XL " hoặc "x l"  ❌ Format không chuẩn
→ Chatbot không match được với database "XL"
```

**New Flow (Buttons - ĐÚNG):**
```
Bot: "What size would you like?"
[Button: M] [Button: L] [Button: XL] [Button: XXL]
User clicks: [XL]  ✅ Guaranteed exact match
→ Chatbot nhận payload "size:XL" → 100% match
```

---

## 🔧 Technical Requirements

### 1. **Rasa Button Message Format**

Chatbot sẽ gửi message có cấu trúc này từ Rasa:

```json
{
  "text": "Chọn size bạn muốn:",
  "buttons": [
    {
      "title": "M",
      "payload": "/inform_size{\"size\":\"M\"}"
    },
    {
      "title": "L",
      "payload": "/inform_size{\"size\":\"L\"}"
    },
    {
      "title": "XL",
      "payload": "/inform_size{\"size\":\"XL\"}"
    },
    {
      "title": "XXL",
      "payload": "/inform_size{\"size\":\"XXL\"}"
    }
  ]
}
```

### 2. **Frontend Display Requirements**

**UI Design:**
```
┌─────────────────────────────────┐
│ Bot:                            │
│ Chọn size bạn muốn:             │
│                                 │
│ ┌───┐ ┌───┐ ┌────┐ ┌─────┐    │
│ │ M │ │ L │ │ XL │ │ XXL │    │
│ └───┘ └───┘ └────┘ └─────┘    │
└─────────────────────────────────┘
```

**Button Styling:**
- Background: White/Light grey
- Border: 1px solid #ddd
- Padding: 8px 16px
- Border-radius: 4px
- Hover: Background → Light blue
- Active/Selected: Background → Blue, Text → White

**Layout:**
- Horizontal layout nếu ≤ 5 buttons
- Grid layout nếu > 5 buttons (2 columns)
- Gap between buttons: 8px

### 3. **Frontend Click Handler**

Khi user click button:

```typescript
// Example implementation
const handleButtonClick = (button: RasaButton) => {
  // Send payload to Rasa
  const message = {
    sender: "user",
    message: button.payload,  // "/inform_size{\"size\":\"XL\"}"
    metadata: {
      button_clicked: true,
      button_title: button.title
    }
  };
  
  // Send to backend
  sendMessageToChatbot(message);
  
  // Display user's choice in chat
  addUserMessage(button.title);  // Show "XL" in chat as user message
  
  // Hide buttons after click
  disableButtonsInMessage(messageId);
};
```

### 4. **Backend API Contract**

**Request to Backend:**
```json
POST /chat/send
{
  "session_id": 23,
  "sender_id": "customer_123",
  "message": "/inform_size{\"size\":\"XL\"}",
  "metadata": {
    "customer_id": 21,
    "button_clicked": true
  }
}
```

**Expected Response:**
```json
{
  "bot_responses": [
    {
      "text": "Size XL selected! Now choose color:",
      "buttons": [
        {
          "title": "Đen",
          "payload": "/inform_color{\"color\":\"Đen\"}"
        },
        {
          "title": "Xám",
          "payload": "/inform_color{\"color\":\"Xám\"}"
        }
      ]
    }
  ]
}
```

---

## 📱 TypeScript Types

```typescript
// Add to your types file
export interface RasaButton {
  title: string;           // Display text
  payload: string;         // Rasa intent + entities
}

export interface RasaMessage {
  text: string;
  buttons?: RasaButton[];  // Optional buttons array
  image?: string;
  metadata?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  session_id: number;
  sender: "bot" | "customer";
  message: string;
  buttons?: RasaButton[];  // Add buttons support
  is_read: boolean;
  created_at: string;
}
```

---

## 🎨 UI Component Example (React)

```tsx
// ChatMessage.tsx
interface ChatMessageProps {
  message: ChatMessage;
  onButtonClick: (button: RasaButton) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, onButtonClick }) => {
  return (
    <div className="chat-message">
      <div className="message-text">{message.message}</div>
      
      {message.buttons && message.buttons.length > 0 && (
        <div className="message-buttons">
          {message.buttons.map((button, index) => (
            <button
              key={index}
              className="rasa-button"
              onClick={() => onButtonClick(button)}
              disabled={message.buttons_disabled}
            >
              {button.title}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
```

**CSS:**
```css
.message-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.rasa-button {
  padding: 8px 16px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.rasa-button:hover:not(:disabled) {
  background: #e3f2fd;
  border-color: #2196f3;
}

.rasa-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

## 🔄 Complete Flow Example

### Step 1: Size Selection

**Bot sends:**
```json
{
  "text": "Chọn size:",
  "buttons": [
    {"title": "M", "payload": "/inform_size{\"size\":\"M\"}"},
    {"title": "L", "payload": "/inform_size{\"size\":\"L\"}"},
    {"title": "XL", "payload": "/inform_size{\"size\":\"XL\"}"}
  ]
}
```

**Frontend displays:** 3 buttons

**User clicks:** [XL]

**Frontend sends:** 
```json
{
  "message": "/inform_size{\"size\":\"XL\"}",
  "metadata": {"button_clicked": true}
}
```

**Frontend displays in chat:**
```
User: XL
```

### Step 2: Color Selection (Filtered by Size)

**Bot sends:**
```json
{
  "text": "Size XL - Các màu có sẵn:",
  "buttons": [
    {"title": "Đen", "payload": "/inform_color{\"color\":\"Đen\"}"},
    {"title": "Xám", "payload": "/inform_color{\"color\":\"Xám\"}"}
  ]
}
```

**User clicks:** [Đen]

**Frontend sends:**
```json
{
  "message": "/inform_color{\"color\":\"Đen\"}",
  "metadata": {"button_clicked": true}
}
```

### Step 3: Confirmation

**Bot sends:**
```json
{
  "text": "✅ Added Áo Blazer (XL, Đen) to cart!",
  "buttons": [
    {"title": "Continue Shopping", "payload": "/search_products"},
    {"title": "View Cart", "payload": "/view_cart"}
  ]
}
```

---

## 📊 Benefits

1. **No More Matching Errors**
   - User chọn từ danh sách → 100% exact match
   - Không còn "XL" vs "xl" vs "X L" issues

2. **Better UX**
   - User không cần gõ → Faster
   - Visual options → Easier to choose
   - Mobile-friendly → Click thay vì type

3. **Data Consistency**
   - Chatbot guarantee giá trị từ database
   - Không có typos từ user
   - Variants matching 100% accurate

---

## ✅ Implementation Checklist

### Frontend Team:
- [ ] Add `buttons` field to `ChatMessage` type
- [ ] Update chat UI component to render buttons
- [ ] Implement button click handler
- [ ] Send button payload to backend correctly
- [ ] Display user's selection in chat after click
- [ ] Disable buttons after click (prevent double click)
- [ ] Style buttons according to design specs
- [ ] Test on mobile devices

### Backend Team (Chat Proxy):
- [ ] Forward button payload to Rasa correctly
- [ ] Preserve metadata when forwarding
- [ ] Return buttons in response if Rasa provides them
- [ ] Test button flow end-to-end

### Chatbot Team:
- [ ] Implement button generation in actions
- [ ] Filter options by selected size
- [ ] Test button payloads
- [ ] Handle button responses correctly

---

## 🧪 Testing Requirements

### Test Cases:

**TC1: Size Button Display**
- User: "add to cart"
- Bot: Shows size buttons (M, L, XL, XXL)
- Expected: 4 buttons displayed horizontally

**TC2: Size Button Click**
- User clicks: [XL]
- Expected: 
  - Frontend sends `/inform_size{"size":"XL"}` to backend
  - User sees "XL" in chat
  - Buttons become disabled

**TC3: Color Button Display (Filtered)**
- After selecting XL
- Bot: Shows only colors available for size XL
- Expected: Only 2-3 buttons (not all colors)

**TC4: Color Button Click**
- User clicks: [Đen]
- Expected:
  - Frontend sends `/inform_color{"color":"Đen"}`
  - Cart adds correct variant (XL + Đen)
  - Confirmation message shown

**TC5: Mobile Responsiveness**
- Test on mobile screen
- Expected: Buttons wrap properly, touch-friendly size

---

## 📝 API Documentation Update Needed

Update `/chat/send` endpoint docs to include:

```
Response Format:
{
  "bot_responses": [
    {
      "message": "string",
      "buttons": [                    // NEW: Optional buttons array
        {
          "title": "string",          // Display text
          "payload": "string"         // Rasa intent + entities
        }
      ]
    }
  ]
}
```

---

## 🚀 Deployment Order

1. **Phase 1:** Frontend implements button UI (no functionality)
2. **Phase 2:** Backend adds button forwarding to Rasa
3. **Phase 3:** Chatbot implements button generation logic
4. **Phase 4:** End-to-end testing
5. **Phase 5:** Deploy to production

---

## 📞 Contact

**Questions?**
- Chatbot Team: See implementation in `actions/actions.py` → `ActionAddToCart`
- Backend Team: Check button forwarding in chat proxy
- Frontend Team: Implement according to specs above

---

**Priority:** HIGH - Blocks add to cart UX improvement  
**ETA:** 2-3 days for complete implementation  
**Status:** 🟡 Pending frontend implementation
