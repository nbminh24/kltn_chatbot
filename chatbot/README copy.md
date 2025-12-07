# 🤖 Chatbot Internal APIs Module

## Overview

This module provides **internal APIs** for the Rasa chatbot server to perform actions on behalf of customers. These APIs bypass JWT authentication and use an internal API key for security.

## Security

All endpoints are protected by `InternalApiKeyGuard` which validates the `X-Internal-Api-Key` header.

**⚠️ IMPORTANT:** These APIs should **NEVER** be exposed to the public internet. They are intended for internal communication between the Rasa server and the backend only.

## Environment Variables

Required environment variables (add to `.env`):

```env
# Internal API Key (use strong random key in production)
INTERNAL_API_KEY=your-super-secret-key-here

# Size Chart URLs
SIZE_CHART_SHIRT_URL=https://cdn.yoursite.com/size-charts/shirt.png
SIZE_CHART_PANTS_URL=https://cdn.yoursite.com/size-charts/pants.png
SIZE_CHART_SHOES_URL=https://cdn.yoursite.com/size-charts/shoes.png
```

## Available Endpoints

### Cart Operations

#### `POST /api/chatbot/cart/add`
Add item to customer cart.

**Headers:**
- `X-Internal-Api-Key: {your-api-key}`

**Request Body:**
```json
{
  "customer_id": 123,
  "variant_id": 456,
  "quantity": 1
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "cart_id": 789,
    "item_id": 101,
    "total_items": 3
  },
  "message": "Item added to cart successfully"
}
```

---

### Wishlist Operations

#### `POST /api/chatbot/wishlist/add`
Add item to customer wishlist.

**Headers:**
- `X-Internal-Api-Key: {your-api-key}`

**Request Body:**
```json
{
  "customer_id": 123,
  "variant_id": 456
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "wishlist_item_id": 202
  },
  "message": "Item added to wishlist successfully"
}
```

---

### Order Operations

#### `POST /api/chatbot/orders/:id/cancel`
Cancel customer order (only pending orders).

**Headers:**
- `X-Internal-Api-Key: {your-api-key}`

**Request Body:**
```json
{
  "customer_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "order_id": 456,
    "status": "cancelled"
  },
  "message": "Order cancelled successfully"
}
```

---

### Size Consultation

#### `GET /api/chatbot/size-chart/:category`
Get size chart image URL for product category.

**Parameters:**
- `category`: `shirt`, `pants`, or `shoes`

**Headers:**
- `X-Internal-Api-Key: {your-api-key}`

**Response:**
```json
{
  "success": true,
  "data": {
    "category": "shirt",
    "image_url": "https://cdn.yoursite.com/size-charts/shirt.png",
    "description": "Size chart for shirt"
  }
}
```

#### `POST /api/chatbot/size-advice`
Get personalized size recommendation.

**Headers:**
- `X-Internal-Api-Key: {your-api-key}`

**Request Body:**
```json
{
  "height": 170,
  "weight": 65,
  "category": "shirt"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "recommended_size": "M",
    "confidence": "high",
    "reason": "Based on your height and weight measurements",
    "note": "This is a general recommendation. Please check the size chart for accurate measurements.",
    "measurements": {
      "height": "170 cm",
      "weight": "65 kg"
    }
  }
}
```

---

### Product Recommendations

#### `GET /api/chatbot/products/recommend`
Get product recommendations based on context/occasion.

**Headers:**
- `X-Internal-Api-Key: {your-api-key}`

**Query Parameters:**
```
context: wedding | beach | work | party | casual | sport (optional)
category: shirt | pants | shoes (optional)
limit: number (default: 5, max: 20)
```

**Example Request:**
```
GET /api/chatbot/products/recommend?context=wedding&category=shirt&limit=5
```

**Response:**
```json
{
  "success": true,
  "data": {
    "context": "wedding",
    "total": 5,
    "recommendations": [
      {
        "product_id": 123,
        "name": "Elegant Wedding Shirt",
        "slug": "elegant-wedding-shirt",
        "description": "Perfect for weddings",
        "price": 299000,
        "thumbnail": "https://...",
        "rating": 4.8,
        "reviews": 42,
        "category": "Shirts",
        "in_stock": true,
        "attributes": {
          "occasion": "wedding",
          "style": "formal"
        }
      }
    ]
  }
}
```

---

### Gemini AI Integration

#### `POST /api/chatbot/gemini/ask`
Ask Google Gemini AI for fashion advice and general questions.

**Headers:**
- `X-Internal-Api-Key: {your-api-key}`

**Request Body:**
```json
{
  "question": "What is the best fabric for summer clothing?"
}
```

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "question": "What is the best fabric for summer clothing?",
    "answer": "For summer clothing, lightweight and breathable fabrics like cotton, linen, and bamboo are ideal. They help keep you cool and comfortable in hot weather.",
    "source": "Gemini AI"
  }
}
```

**Response (Fallback on Error):**
```json
{
  "success": true,
  "data": {
    "question": "What is the best fabric for summer clothing?",
    "answer": "I'm sorry, I couldn't process your question right now. Please try asking something else or contact our support team for assistance.",
    "source": "Fallback",
    "error": true
  }
}
```

---

## Error Responses

All endpoints return standardized error responses:

### 401 Unauthorized
Missing or invalid API key.

```json
{
  "statusCode": 401,
  "message": "Invalid or missing internal API key",
  "error": "Unauthorized"
}
```

### 404 Not Found
Resource not found (customer, product variant, order, etc.).

```json
{
  "statusCode": 404,
  "message": "Customer with ID 123 not found",
  "error": "Not Found"
}
```

### 400 Bad Request
Validation error or business rule violation.

```json
{
  "statusCode": 400,
  "message": "Insufficient stock. Only 5 items available",
  "error": "Bad Request"
}
```

---

## Testing

### Using cURL

```bash
# Test add to cart
curl -X POST http://localhost:3001/api/chatbot/cart/add \
  -H "Content-Type: application/json" \
  -H "X-Internal-Api-Key: your-api-key" \
  -d '{
    "customer_id": 1,
    "variant_id": 2,
    "quantity": 1
  }'

# Test size chart
curl -X GET http://localhost:3001/api/chatbot/size-chart/shirt \
  -H "X-Internal-Api-Key: your-api-key"

# Test size advice
curl -X POST http://localhost:3001/api/chatbot/size-advice \
  -H "Content-Type: application/json" \
  -H "X-Internal-Api-Key: your-api-key" \
  -d '{
    "height": 170,
    "weight": 65
  }'
```

### Using Postman

1. Import collection from `docs/postman/chatbot-internal-apis.json`
2. Set environment variable `INTERNAL_API_KEY`
3. Run requests

---

## Rasa Integration

### Example Action (Python)

```python
import requests
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List

BACKEND_URL = "http://localhost:3001"
INTERNAL_API_KEY = "your-api-key"

class ActionAddToCart(Action):
    def name(self) -> Text:
        return "action_add_to_cart"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        customer_id = tracker.get_slot("customer_id")
        variant_id = tracker.get_slot("current_variant_id")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/chatbot/cart/add",
                json={
                    "customer_id": customer_id,
                    "variant_id": variant_id,
                    "quantity": 1
                },
                headers={"X-Internal-Api-Key": INTERNAL_API_KEY},
                timeout=10
            )
            response.raise_for_status()
            
            dispatcher.utter_message(text="Added to cart! 🛒")
            return []
            
        except Exception as e:
            dispatcher.utter_message(
                text="Sorry, I couldn't add this to your cart. Please try again."
            )
            return []
```

---

## Architecture

```
┌─────────────────┐
│  Rasa Server    │
│  (Python)       │
└────────┬────────┘
         │ X-Internal-Api-Key
         ▼
┌─────────────────────────┐
│  Backend (NestJS)       │
│                         │
│  InternalApiKeyGuard    │ ← Validates API key
│         │               │
│         ▼               │
│  ChatbotController      │ ← Handles requests
│         │               │
│         ▼               │
│  ChatbotService         │ ← Business logic
│         │               │
│         ▼               │
│  Existing Services      │ ← Reuses CartService,
│  (Cart, Order, etc.)    │   OrdersService, etc.
└─────────────────────────┘
```

---

## Development

### Run tests

```bash
npm run test src/modules/chatbot
```

### Generate test coverage

```bash
npm run test:cov src/modules/chatbot
```

---

## Deployment

### Production Checklist

- [ ] Change `INTERNAL_API_KEY` to strong random key (minimum 32 characters)
- [ ] Store API key in secrets manager (not in `.env` file)
- [ ] Configure firewall to only allow Rasa server IP
- [ ] Setup API Gateway to restrict access
- [ ] Enable rate limiting
- [ ] Setup monitoring alerts
- [ ] Configure logging for audit trail

---

## Support

For issues or questions, contact the backend team.

**Created:** 2024-12-07  
**Version:** 1.0
