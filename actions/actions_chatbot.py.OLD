"""
Custom Actions for Chatbot - Using NEW Backend Internal APIs
These actions use the chatbot-specific endpoints (/api/chatbot/*)
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
import logging

from .api_client import get_api_client

logger = logging.getLogger(__name__)


# ============================================================================
# CART & PURCHASE ACTIONS - Using Internal Chatbot APIs
# ============================================================================

class ActionAddToCart(Action):
    """
    Add product to cart using internal chatbot API
    Requires: customer_id, variant_id, quantity
    Slot filling: size, color needed to determine variant_id
    """
    
    def name(self) -> Text:
        return "action_add_to_cart"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Get customer_id from slot (set by frontend)
        customer_id = tracker.get_slot("customer_id")
        
        if not customer_id:
            dispatcher.utter_message(
                text="Bạn cần đăng nhập để thêm sản phẩm vào giỏ hàng nhé! 🔐"
            )
            return []
        
        # Get product context
        current_product_id = tracker.get_slot("current_product_id")
        
        if not current_product_id:
            dispatcher.utter_message(
                text="Bạn muốn thêm sản phẩm nào vào giỏ hàng? Hãy chọn sản phẩm trước nhé! 😊"
            )
            return []
        
        # Check if we have size and color (slot filling)
        cart_size = tracker.get_slot("cart_size")
        cart_color = tracker.get_slot("cart_color")
        
        # If missing size, ask for it
        if not cart_size:
            dispatcher.utter_message(
                text="Bạn muốn size nào nhỉ? (S, M, L, XL)"
            )
            return []
        
        # If missing color, ask for it
        if not cart_color:
            dispatcher.utter_message(
                text="Bạn thích màu nào? (Đen, Trắng, Xanh, Đỏ...)"
            )
            return []
        
        # Get quantity (default 1)
        quantity = tracker.get_slot("cart_quantity") or 1
        
        # TODO: Need to get variant_id from product_id + size + color
        # For now, we need backend to provide an endpoint to get variant by attributes
        # OR we get product details first which includes variants
        
        api_client = get_api_client()
        
        # Get product details to find variant_id
        product_result = api_client.get_product_by_id(str(current_product_id))
        
        if product_result.get("error"):
            dispatcher.utter_message(
                text="Xin lỗi, không thể lấy thông tin sản phẩm. Vui lòng thử lại sau! 🙏"
            )
            return []
        
        # Find matching variant (this logic depends on backend response structure)
        # Assuming product has 'variants' array
        variants = product_result.get("variants", [])
        variant_id = None
        
        for variant in variants:
            v_size = variant.get("size", {}).get("name", "").lower()
            v_color = variant.get("color", {}).get("name", "").lower()
            
            if v_size == str(cart_size).lower() and v_color == str(cart_color).lower():
                variant_id = variant.get("id")
                break
        
        if not variant_id:
            dispatcher.utter_message(
                text=f"Xin lỗi, không tìm thấy sản phẩm với size {cart_size} màu {cart_color}. Bạn có thể chọn size/màu khác không? 🤔"
            )
            return []
        
        # Call internal chatbot API to add to cart
        result = api_client.add_to_cart(
            customer_id=int(customer_id),
            variant_id=variant_id,
            quantity=int(quantity)
        )
        
        if result.get("error"):
            dispatcher.utter_message(
                text="Không thể thêm vào giỏ hàng lúc này. Vui lòng thử lại sau! 😔"
            )
            return []
        
        dispatcher.utter_message(
            text=f"✅ Đã thêm vào giỏ hàng! Size {cart_size}, màu {cart_color}, số lượng {quantity}.\n\nBạn có muốn xem giỏ hàng hoặc tiếp tục mua sắm không? 🛒"
        )
        
        # Reset slot filling slots
        return [
            SlotSet("cart_size", None),
            SlotSet("cart_color", None),
            SlotSet("cart_quantity", 1)
        ]


class ActionAddToWishlist(Action):
    """Add product to wishlist using internal chatbot API"""
    
    def name(self) -> Text:
        return "action_add_to_wishlist"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        customer_id = tracker.get_slot("customer_id")
        
        if not customer_id:
            dispatcher.utter_message(
                text="Bạn cần đăng nhập để lưu sản phẩm yêu thích! 💖"
            )
            return []
        
        current_variant_id = tracker.get_slot("current_variant_id")
        
        if not current_variant_id:
            dispatcher.utter_message(
                text="Bạn muốn lưu sản phẩm nào? Hãy chọn sản phẩm trước nhé!"
            )
            return []
        
        api_client = get_api_client()
        result = api_client.add_to_wishlist(
            customer_id=int(customer_id),
            variant_id=int(current_variant_id)
        )
        
        if result.get("error"):
            dispatcher.utter_message(
                text="Không thể thêm vào danh sách yêu thích. Vui lòng thử lại!"
            )
            return []
        
        dispatcher.utter_message(
            text="❤️ Đã lưu vào danh sách yêu thích! Bạn có thể xem lại sau trong trang Wishlist của mình."
        )
        
        return []


class ActionBuyNow(Action):
    """
    Redirect user to checkout page (frontend handling)
    Bot provides information for frontend to handle redirect
    """
    
    def name(self) -> Text:
        return "action_buy_now"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        current_product_id = tracker.get_slot("current_product_id")
        current_variant_id = tracker.get_slot("current_variant_id")
        
        if not current_product_id:
            dispatcher.utter_message(
                text="Bạn muốn mua sản phẩm nào? Hãy chọn sản phẩm trước nhé!"
            )
            return []
        
        # Return custom response that frontend can handle to redirect
        dispatcher.utter_message(
            text="Chuyển đến trang thanh toán... 🛍️",
            json_message={
                "action": "redirect_checkout",
                "product_id": current_product_id,
                "variant_id": current_variant_id
            }
        )
        
        return []


# ============================================================================
# ORDER MANAGEMENT - Using Internal Chatbot APIs
# ============================================================================

class ActionCancelOrder(Action):
    """Cancel order using internal chatbot API"""
    
    def name(self) -> Text:
        return "action_cancel_order"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        customer_id = tracker.get_slot("customer_id")
        
        if not customer_id:
            dispatcher.utter_message(
                text="Bạn cần đăng nhập để hủy đơn hàng!"
            )
            return []
        
        # Get order_id from entity or slot
        order_id = next(tracker.get_latest_entity_values("order_id"), None)
        if not order_id:
            order_id = tracker.get_slot("last_order_id")
        
        if not order_id:
            dispatcher.utter_message(
                text="Bạn muốn hủy đơn hàng nào? Vui lòng cho mình mã đơn hàng!"
            )
            return []
        
        api_client = get_api_client()
        result = api_client.cancel_order(
            order_id=int(order_id),
            customer_id=int(customer_id)
        )
        
        if result.get("error"):
            error_msg = result.get("message", "")
            if "cannot be cancelled" in error_msg.lower():
                dispatcher.utter_message(
                    text="Đơn hàng này không thể hủy vì đã được xử lý. Bạn có thể từ chối nhận hàng hoặc liên hệ hỗ trợ để được giúp đỡ!"
                )
            else:
                dispatcher.utter_message(
                    text="Không thể hủy đơn hàng lúc này. Vui lòng liên hệ hỗ trợ!"
                )
            return []
        
        dispatcher.utter_message(
            text=f"✅ Đơn hàng #{order_id} đã được hủy thành công! Nếu đã thanh toán, tiền sẽ được hoàn lại trong 5-7 ngày làm việc."
        )
        
        return [SlotSet("last_order_id", None)]


class ActionCreateFeedbackTicket(Action):
    """Create feedback/complaint ticket for order issues"""
    
    def name(self) -> Text:
        return "action_create_feedback_ticket"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        order_id = next(tracker.get_latest_entity_values("order_id"), None)
        issue_type = next(tracker.get_latest_entity_values("issue_type"), "general_feedback")
        user_message = tracker.latest_message.get("text", "")
        
        subject = f"Feedback về đơn hàng #{order_id}" if order_id else "Feedback từ khách hàng"
        message = f"Khách hàng phản hồi về đơn hàng:\n\nNội dung: {user_message}\n\nLoại vấn đề: {issue_type}"
        
        api_client = get_api_client()
        result = api_client.create_support_ticket(
            subject=subject,
            message=message,
            user_message=user_message
        )
        
        if result.get("error"):
            dispatcher.utter_message(
                text="Mình đã ghi nhận phản hồi của bạn. Đội hỗ trợ sẽ liên hệ trong 24h! 🎫"
            )
        else:
            dispatcher.utter_message(
                text="Cảm ơn bạn đã phản hồi! Mình rất xin lỗi về sự cố này. Đã tạo ticket hỗ trợ và đội ngũ sẽ liên hệ bạn sớm nhất! 🙏"
            )
        
        return []


# ============================================================================
# SIZE & CONSULTATION - Using Internal Chatbot APIs
# ============================================================================

class ActionGetSizeChart(Action):
    """Get size chart using internal chatbot API"""
    
    def name(self) -> Text:
        return "action_get_size_chart"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Get category from entity or context
        category = next(tracker.get_latest_entity_values("category"), None)
        
        # Map category names to API values
        category_map = {
            "áo": "shirt",
            "ao": "shirt",
            "shirt": "shirt",
            "quần": "pants",
            "quan": "pants",
            "pants": "pants",
            "giày": "shoes",
            "giay": "shoes",
            "shoes": "shoes"
        }
        
        if not category:
            dispatcher.utter_message(
                text="Bạn muốn xem bảng size của loại sản phẩm nào? (Áo, Quần, Giày)"
            )
            return []
        
        api_category = category_map.get(str(category).lower(), "shirt")
        
        api_client = get_api_client()
        result = api_client.get_size_chart(api_category)
        
        if result.get("error"):
            dispatcher.utter_message(text="Xin lỗi, không thể lấy bảng size lúc này. Vui lòng thử lại!")
            return []
        
        data = result.get("data", {})
        image_url = data.get("image_url")
        description = data.get("description", "")
        
        if image_url:
            dispatcher.utter_message(
                text=f"📏 {description}\n\nXem bảng size tại: {image_url}"
            )
        else:
            dispatcher.utter_message(
                text="Bảng size chưa sẵn sàng. Bạn có thể cho mình chiều cao và cân nặng để tư vấn size phù hợp!"
            )
        
        return []


class ActionGetSizingAdvice(Action):
    """Get personalized sizing advice using internal chatbot API"""
    
    def name(self) -> Text:
        return "action_get_sizing_advice"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Extract height and weight from entities
        height = next(tracker.get_latest_entity_values("height"), None)
        weight = next(tracker.get_latest_entity_values("weight"), None)
        category = next(tracker.get_latest_entity_values("category"), "shirt")
        
        # Parse numbers from text if needed
        if height:
            # Extract number from string like "1m7", "170cm", "170"
            import re
            height_match = re.search(r'(\d+)', str(height))
            if height_match:
                height = int(height_match.group(1))
                # Convert 17 -> 170, 175 stays 175
                if height < 100:
                    height = height * 10
        
        if weight:
            weight_match = re.search(r'(\d+)', str(weight))
            if weight_match:
                weight = int(weight_match.group(1))
        
        if not height or not weight:
            dispatcher.utter_message(
                text="Để tư vấn size chính xác, bạn cho mình biết chiều cao và cân nặng nhé! Ví dụ: 'Mình cao 1m7, nặng 65kg'"
            )
            return []
        
        api_client = get_api_client()
        result = api_client.get_sizing_advice(
            height=height,
            weight=weight,
            category=str(category)
        )
        
        if result.get("error"):
            # Fallback to simple logic
            if height >= 175 and weight >= 70:
                size = "L hoặc XL"
            elif height >= 165 and weight >= 60:
                size = "M hoặc L"
            else:
                size = "S hoặc M"
            
            dispatcher.utter_message(
                text=f"Với chiều cao {height}cm và cân nặng {weight}kg, mình nghĩ bạn nên chọn size {size}. Tuy nhiên bạn nên xem bảng size chi tiết để chắc chắn nhé! 📏"
            )
            return []
        
        data = result.get("data", {})
        recommended_size = data.get("recommended_size")
        confidence = data.get("confidence")
        reason = data.get("reason", "")
        note = data.get("note", "")
        
        response = f"📏 **Tư vấn size cho bạn:**\n\n"
        response += f"✅ Size đề nghị: **{recommended_size}**\n"
        response += f"🎯 Độ chính xác: {confidence}\n\n"
        if reason:
            response += f"{reason}\n\n"
        if note:
            response += f"💡 Lưu ý: {note}"
        
        dispatcher.utter_message(text=response)
        
        return []


# ============================================================================
# PRODUCT RECOMMENDATIONS - Using Internal Chatbot API
# ============================================================================

class ActionRecommendByContext(Action):
    """Recommend products by context/occasion using internal chatbot API"""
    
    def name(self) -> Text:
        return "action_recommend_by_context"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Get context/occasion from entities
        context = next(tracker.get_latest_entity_values("context"), None)
        occasion = next(tracker.get_latest_entity_values("occasion"), None)
        category = next(tracker.get_latest_entity_values("category"), None)
        
        search_context = context or occasion
        
        if not search_context:
            dispatcher.utter_message(
                text="Bạn cần trang phục cho dịp gì nhỉ? (Đi làm, đám cưới, đi biển, dạo phố, thể thao...)"
            )
            return []
        
        # Map Vietnamese context to English
        context_map = {
            "đám cưới": "wedding",
            "dam cuoi": "wedding",
            "wedding": "wedding",
            "đi biển": "beach",
            "di bien": "beach",
            "beach": "beach",
            "đi làm": "work",
            "di lam": "work",
            "work": "work",
            "văn phòng": "work",
            "van phong": "work",
            "tiệc": "party",
            "party": "party",
            "dạo phố": "casual",
            "dao pho": "casual",
            "casual": "casual",
            "thể thao": "sport",
            "the thao": "sport",
            "sport": "sport"
        }
        
        api_context = context_map.get(str(search_context).lower(), str(search_context))
        
        api_client = get_api_client()
        result = api_client.get_product_recommendations(
            context=api_context,
            category=str(category) if category else None,
            limit=5
        )
        
        if result.get("error"):
            dispatcher.utter_message(
                text="Xin lỗi, không thể gợi ý sản phẩm lúc này. Bạn có thể tìm kiếm trực tiếp hoặc xem sản phẩm mới nhất!"
            )
            return []
        
        data = result.get("data", {})
        recommendations = data.get("recommendations", [])
        total = data.get("total", 0)
        
        if not recommendations:
            dispatcher.utter_message(
                text=f"Hiện chưa có gợi ý phù hợp cho {search_context}. Bạn có thể xem các sản phẩm phổ biến hoặc mới nhất!"
            )
            return []
        
        response = f"✨ **Gợi ý outfit cho {search_context}:**\n\n"
        
        for i, product in enumerate(recommendations[:5], 1):
            name = product.get("name", "")
            price = product.get("price", 0)
            rating = product.get("rating", 0)
            in_stock = product.get("in_stock", True)
            
            price_str = f"{price:,.0f}₫" if price > 0 else "Liên hệ"
            stock_emoji = "✅" if in_stock else "❌"
            
            response += f"{i}. **{name}**\n"
            response += f"   💰 {price_str} | ⭐ {rating}/5 | {stock_emoji}\n\n"
        
        response += "Bạn thích món nào? Mình có thể tư vấn thêm về size, màu sắc hoặc cách phối đồ! 😊"
        
        dispatcher.utter_message(text=response)
        
        return [SlotSet("last_products", recommendations)]


# ============================================================================
# PROMOTIONS - Using Internal/Public APIs
# ============================================================================

class ActionGetPromotions(Action):
    """Get active promotions"""
    
    def name(self) -> Text:
        return "action_get_promotions"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # This would call a promotions endpoint
        # For now, use fallback response
        dispatcher.utter_message(
            text="🎉 **Khuyến mãi đang diễn ra:**\n\n"
                 "• Giảm 20% cho đơn hàng trên 500k\n"
                 "• Freeship toàn quốc cho đơn từ 300k\n"
                 "• Mua 2 tặng 1 cho áo thun basic\n\n"
                 "Nhập mã: **FASHION20** khi thanh toán! 🛍️"
        )
        
        return []


# ============================================================================
# GEMINI AI FALLBACK - Using Internal Chatbot API
# ============================================================================

class ActionAskGemini(Action):
    """Handle out-of-scope questions using Gemini AI"""
    
    def name(self) -> Text:
        return "action_ask_gemini"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get("text", "")
        
        if not user_message:
            dispatcher.utter_message(text="Bạn muốn hỏi gì ạ?")
            return []
        
        api_client = get_api_client()
        result = api_client.ask_gemini(question=user_message)
        
        if result.get("error"):
            dispatcher.utter_message(
                text="Xin lỗi, câu hỏi này hơi khó với mình. Bạn có thể hỏi về sản phẩm, đơn hàng hoặc chính sách của shop không? 😊"
            )
            return []
        
        data = result.get("data", {})
        answer = data.get("answer", "")
        source = data.get("source", "")
        
        if answer:
            response = f"{answer}\n\n"
            if "gemini" in source.lower():
                response += "_(Được hỗ trợ bởi Gemini AI)_\n\n"
            response += "Nhân tiện, bạn có cần tìm sản phẩm gì không? 🛍️"
            
            dispatcher.utter_message(text=response)
        else:
            dispatcher.utter_message(
                text="Mình chưa hiểu câu hỏi này lắm. Bạn có thể hỏi về thời trang, sản phẩm hoặc đơn hàng của mình không?"
            )
        
        return []


# ============================================================================
# PRODUCT INFO & STOCK CHECK
# ============================================================================

class ActionGetProductInfo(Action):
    """Get specific product information (material, price, origin)"""
    
    def name(self) -> Text:
        return "action_get_product_info"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        current_product_id = tracker.get_slot("current_product_id")
        info_type = next(tracker.get_latest_entity_values("info_type"), "all")
        
        if not current_product_id:
            dispatcher.utter_message(
                text="Bạn muốn xem thông tin của sản phẩm nào? Hãy chọn sản phẩm trước nhé!"
            )
            return []
        
        api_client = get_api_client()
        result = api_client.get_product_by_id(str(current_product_id))
        
        if result.get("error"):
            dispatcher.utter_message(text="Không thể lấy thông tin sản phẩm. Vui lòng thử lại!")
            return []
        
        product = result.get("data", result)
        
        # Extract info based on type
        if info_type == "material":
            material = product.get("attributes", {}).get("material", "Chưa cập nhật")
            dispatcher.utter_message(text=f"Chất liệu: {material}")
        elif info_type == "price":
            price = product.get("selling_price", 0)
            dispatcher.utter_message(text=f"Giá: {price:,.0f}₫")
        elif info_type == "origin":
            origin = product.get("attributes", {}).get("origin", "Chưa cập nhật")
            dispatcher.utter_message(text=f"Xuất xứ: {origin}")
        else:
            # Show all info
            name = product.get("name", "")
            price = product.get("selling_price", 0)
            description = product.get("description", "")
            
            response = f"**{name}**\n\n"
            response += f"💰 Giá: {price:,.0f}₫\n"
            response += f"📝 {description[:200]}...\n\n"
            response += "Bạn muốn biết thêm gì không?"
            
            dispatcher.utter_message(text=response)
        
        return []


class ActionCheckStock(Action):
    """Check product stock availability"""
    
    def name(self) -> Text:
        return "action_check_stock"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        product_name = next(tracker.get_latest_entity_values("product_name"), None)
        size = next(tracker.get_latest_entity_values("size"), None)
        color = next(tracker.get_latest_entity_values("color"), None)
        
        # Get from context if not in entities
        if not product_name:
            last_products = tracker.get_slot("last_products")
            if last_products and len(last_products) > 0:
                product_name = last_products[0].get("name")
        
        if not product_name:
            dispatcher.utter_message(
                text="Bạn muốn kiểm tra tồn kho của sản phẩm nào?"
            )
            return []
        
        api_client = get_api_client()
        result = api_client.check_product_availability(
            product_name=product_name,
            size=str(size) if size else None,
            color=str(color) if color else None
        )
        
        if result.get("error"):
            dispatcher.utter_message(
                text=f"Không thể kiểm tra tồn kho cho {product_name}. Vui lòng thử lại!"
            )
            return []
        
        # Parse availability response
        data = result.get("data", [])
        
        if not data:
            dispatcher.utter_message(
                text=f"Hiện không có sản phẩm '{product_name}' trong kho. Bạn có muốn xem sản phẩm tương tự không?"
            )
            return []
        
        # Show availability
        response = f"📦 **Tình trạng kho '{product_name}':**\n\n"
        for item in data[:5]:
            item_size = item.get("size", "N/A")
            item_color = item.get("color", "N/A")
            stock = item.get("stock", 0)
            
            status = "✅ Còn hàng" if stock > 0 else "❌ Hết hàng"
            response += f"• Size {item_size} - Màu {item_color}: {status}\n"
        
        dispatcher.utter_message(text=response)
        
        return []
