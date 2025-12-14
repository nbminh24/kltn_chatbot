# Chatbot Update Request: Product Actions Metadata Support

**Date:** 2025-12-13  
**Priority:** 🔴 CRITICAL  
**Requested by:** Frontend Team  
**Issue:** Add-to-cart variant matching failure (bug report: `BUG_REPORT_ADD_TO_CART_VARIANT_MISMATCH.md`)

---

## 📋 Summary

Chatbot cần update để:
1. Gửi metadata `product_actions` khi user hỏi về product details
2. Nhận metadata từ frontend với `color_id` và `size_id` khi add to cart
3. Match variant bằng IDs thay vì text để tránh lỗi matching

---

## 🎯 Why This Update is Needed

**Current Problem:**
- User types: "XXL" nhưng backend có "2XL" → Không match được
- User types: "black" nhưng backend có "Black" → Case-sensitive fail
- Chatbot falls back to `product_id` → **Wrong variant added to cart**

**Solution:**
- Frontend hiển thị buttons cho color/size
- User clicks buttons → Frontend gửi `color_id=1, size_id=14`
- Chatbot match by IDs → **100% accurate, no more errors**

---

## 🔧 Changes Required in actions.py

### **File:** `actions/actions.py`

---

## 📝 Change 1: Update ActionGetProductDetails

### **Location:** Class `ActionGetProductDetails` → method `run()`

### **Current Code (Around line 1340):**

```python
response += f"📝 **Description:**\n{description}\n\n"

# CTA based on stock status
if in_stock:
    response += "Would you like sizing advice, styling tips, or ready to add to cart? 😊"
else:
    response += "This item is out of stock. Would you like me to suggest similar products?"

dispatcher.utter_message(text=response)
```

### **New Code (Replace with this):**

```python
response += f"📝 **Description:**\n{description}\n\n"

# CTA based on stock status
if in_stock:
    response += "Would you like to add this to your cart? 😊"
else:
    response += "This item is out of stock. Would you like me to suggest similar products?"

# NEW: Send product_actions metadata for button-based variant selection
custom_data = None
if in_stock and variants and len(variants) > 0:
    # Extract unique colors and sizes with IDs
    colors_map = {}
    sizes_map = {}
    
    for v in variants:
        # Extract color info
        color_obj = v.get("color", {})
        if isinstance(color_obj, dict):
            color_id = color_obj.get("id") or v.get("color_id")
            color_name = color_obj.get("name") or v.get("color_name")
            color_hex = color_obj.get("hex") or v.get("color_hex")
            
            if color_id and color_name and color_id not in colors_map:
                colors_map[color_id] = {
                    "id": int(color_id),
                    "name": str(color_name),
                    "hex": str(color_hex) if color_hex else None
                }
        
        # Extract size info
        size_obj = v.get("size", {})
        if isinstance(size_obj, dict):
            size_id = size_obj.get("id") or v.get("size_id")
            size_name = size_obj.get("name") or v.get("size_name")
            
            if size_id and size_name and size_id not in sizes_map:
                sizes_map[size_id] = {
                    "id": int(size_id),
                    "name": str(size_name)
                }
    
    available_colors_with_ids = list(colors_map.values())
    available_sizes_with_ids = list(sizes_map.values())
    
    # Only send metadata if we have both colors and sizes
    if available_colors_with_ids and available_sizes_with_ids:
        custom_data = {
            "type": "product_actions",
            "product_id": int(product_id),
            "product_name": name,
            "product_price": float(price_raw) if price_raw else 0,
            "product_thumbnail": product.get("thumbnail") or product.get("image_url") or "",
            "available_colors": available_colors_with_ids,
            "available_sizes": available_sizes_with_ids
        }
        logger.info(f"✅ Sending product_actions metadata: {len(available_colors_with_ids)} colors, {len(available_sizes_with_ids)} sizes")

dispatcher.utter_message(
    text=response,
    json_message={"custom": custom_data} if custom_data else None
)
```

---

## 📝 Change 2: Update ActionAddToCart

### **Location:** Class `ActionAddToCart` → method `run()`

### **Current Code (First lines of run method):**

```python
def run(
    self,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    domain: Dict[Text, Any]
) -> List[Dict[Text, Any]]:
    
    user_message = tracker.latest_message.get("text", "")
    
    # Get filled slots from form
    product_id = tracker.get_slot("current_product_id")
    size = tracker.get_slot("cart_size")
    color = tracker.get_slot("cart_color")
    quantity = tracker.get_slot("cart_quantity") or 1
```

### **New Code (Replace with this):**

```python
def run(
    self,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    domain: Dict[Text, Any]
) -> List[Dict[Text, Any]]:
    
    user_message = tracker.latest_message.get("text", "")
    metadata = tracker.latest_message.get("metadata", {})
    
    # Check if frontend sent structured metadata with IDs
    if metadata.get("action") == "add_to_cart":
        logger.info(f"✅ Frontend sent structured metadata: {metadata}")
        return self._handle_add_to_cart_with_ids(dispatcher, tracker, metadata)
    
    # Fallback: Old text-based flow
    # Get filled slots from form
    product_id = tracker.get_slot("current_product_id")
    size = tracker.get_slot("cart_size")
    color = tracker.get_slot("cart_color")
    quantity = tracker.get_slot("cart_quantity") or 1
```

---

## 📝 Change 3: Add New Method to ActionAddToCart

### **Location:** Inside class `ActionAddToCart`, at the END of the class (before the closing of the class)

### **Add this new method:**

```python
def _handle_add_to_cart_with_ids(
    self,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    metadata: Dict[Text, Any]
) -> List[Dict[Text, Any]]:
    """
    Handle add-to-cart request with color_id and size_id from frontend.
    This provides 100% accurate variant matching.
    """
    product_id = metadata.get("product_id")
    color_id = metadata.get("color_id")
    size_id = metadata.get("size_id")
    quantity = metadata.get("quantity", 1)
    
    logger.info(f"🛒 Add to cart with IDs: product={product_id}, color_id={color_id}, size_id={size_id}, qty={quantity}")
    
    if not product_id or not color_id or not size_id:
        dispatcher.utter_message(
            text="Sorry, I need product ID, color ID, and size ID to add to cart. Please try again! 😅"
        )
        return []
    
    # Get customer_id
    customer_id = get_customer_id_from_tracker(tracker)
    
    if not customer_id:
        dispatcher.utter_message(
            text="To add items to your cart, please sign in first! 🔐"
        )
        return []
    
    try:
        api_client = get_api_client()
        
        # Get product details
        product_result = api_client.get_product_by_id(str(product_id))
        if product_result.get("error"):
            dispatcher.utter_message(
                text="Sorry, I couldn't find that product. Please try again! 🙏"
            )
            return []
        
        product_data = product_result.get("data", product_result)
        product_name = product_data.get("name", "Product")
        variants = product_data.get("variants", [])
        
        # Find variant by color_id and size_id (100% accurate matching)
        variant_id = None
        variant_info = None
        
        for v in variants:
            # Extract IDs from nested objects
            color_obj = v.get("color", {})
            size_obj = v.get("size", {})
            
            v_color_id = color_obj.get("id") if isinstance(color_obj, dict) else None
            v_size_id = size_obj.get("id") if isinstance(size_obj, dict) else None
            
            # Also try direct fields
            if not v_color_id:
                v_color_id = v.get("color_id")
            if not v_size_id:
                v_size_id = v.get("size_id")
            
            # Match by IDs
            if v_color_id == color_id and v_size_id == size_id:
                variant_id = v.get("id")
                variant_info = {
                    "color_name": color_obj.get("name") if isinstance(color_obj, dict) else "Unknown",
                    "size_name": size_obj.get("name") if isinstance(size_obj, dict) else "Unknown"
                }
                logger.info(f"✅ Found variant by IDs: variant_id={variant_id}, color={variant_info['color_name']}, size={variant_info['size_name']}")
                break
        
        if not variant_id:
            logger.error(f"❌ No variant found for color_id={color_id}, size_id={size_id}")
            dispatcher.utter_message(
                text="Sorry, I couldn't find that specific variant. It might be out of stock. 😅"
            )
            return []
        
        # Add to cart using variant_id
        result = api_client.add_to_cart(
            customer_id=int(customer_id),
            variant_id=int(variant_id),
            quantity=int(quantity)
        )
        
        if isinstance(result, dict) and (result.get("success") or result.get("data")):
            dispatcher.utter_message(
                text=f"✅ Added **{product_name}** ({variant_info['size_name']}, {variant_info['color_name']}) to your cart!\n\n"
                     f"Quantity: {quantity}\n\n"
                     f"Would you like to continue shopping or check out? 🛍️"
            )
            return [
                SlotSet("cart_size", None),
                SlotSet("cart_color", None),
                SlotSet("cart_quantity", 1)
            ]
        else:
            error_msg = result.get("message", result.get("error", "Unknown error"))
            logger.error(f"❌ Backend error: {error_msg}")
            dispatcher.utter_message(
                text=f"Sorry, I couldn't add that to your cart right now. {error_msg} 😅"
            )
            return []
    
    except Exception as e:
        logger.error(f"❌ Exception in add_to_cart with IDs: {e}", exc_info=True)
        dispatcher.utter_message(
            text="Oops! Something went wrong. Please try again! 🙏"
        )
        return []
```

---

## 🧪 Testing Instructions

### 1. Test Product Details Response

**User says:** "i want more info about the first one"

**Expected chatbot response:**
```json
{
  "text": "📦 Product Name\n💰 Price: $12.72\n...",
  "custom": {
    "type": "product_actions",
    "product_id": 7,
    "product_name": "...",
    "available_colors": [
      {"id": 1, "name": "Black", "hex": "#000000"},
      {"id": 2, "name": "White", "hex": "#FFFFFF"}
    ],
    "available_sizes": [
      {"id": 10, "name": "S"},
      {"id": 14, "name": "XXL"}
    ]
  }
}
```

**Check logs:**
```
✅ Sending product_actions metadata: 4 colors, 6 sizes
```

---

### 2. Test Add to Cart with IDs

**Frontend sends to backend:**
```json
POST /chat/send
{
  "session_id": 1,
  "message": "Thêm vào giỏ hàng",
  "metadata": {
    "action": "add_to_cart",
    "product_id": 7,
    "color_id": 1,
    "size_id": 14
  }
}
```

**Expected chatbot logs:**
```
✅ Frontend sent structured metadata: {...}
🛒 Add to cart with IDs: product=7, color_id=1, size_id=14, qty=1
✅ Found variant by IDs: variant_id=123, color=Black, size=XXL
```

**Expected response:**
```
✅ Added **Product Name** (XXL, Black) to your cart!
Quantity: 1
Would you like to continue shopping or check out? 🛍️
```

---

## ✅ Acceptance Criteria

- [ ] `ActionGetProductDetails` gửi metadata với `available_colors` và `available_sizes` (có IDs)
- [ ] Frontend hiển thị buttons (frontend đã ready)
- [ ] User có thể click buttons để chọn variant
- [ ] `ActionAddToCart` nhận metadata với `color_id` và `size_id`
- [ ] Variant matching dùng IDs (100% accurate)
- [ ] Add-to-cart thành công với đúng variant
- [ ] Text-based flow vẫn hoạt động (fallback)

---

## 🚀 Deployment

1. Update `actions/actions.py` theo hướng dẫn trên
2. Restart Rasa action server:
   ```bash
   rasa run actions
   ```
3. Test flow từ đầu đến cuối
4. Check logs để verify metadata được gửi đúng

---

## 📞 Questions?

- Frontend team: Implementation complete, đang chờ chatbot update
- Backend team: API `/internal/products/:id` đã ready với đầy đủ color_id/size_id
- Any issues: Check console logs cho metadata format

**Status:** 🔴 CRITICAL - Cần update ngay để fix variant matching bug
