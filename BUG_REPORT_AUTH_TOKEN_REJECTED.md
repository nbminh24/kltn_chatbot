# 🐛 BUG: Backend Rejecting JWT Token for Order Tracking

## Issue ID: BE-ORDER-AUTH-001
**Severity:** 🔴 CRITICAL  
**Component:** Backend API - Order Tracking Authentication  
**Status:** OPEN  
**Date:** 2025-12-16

---

## 📋 Summary
Backend endpoint `/orders/track` returns **400 Bad Request** with message "Yêu cầu đăng nhập để track order" (Login required) despite chatbot sending a valid JWT token in the Authorization header.

**Impact:** Order tracking feature completely broken - users cannot view any orders.

---

## 🔍 Problem Details

### **Chatbot Logs (Correct ✅)**
```
2025-12-16 11:41:20 INFO  - ✅ Got customer_id from metadata: 1
2025-12-16 11:41:20 INFO  - 🔐 User authenticated - customer_id: 1
2025-12-16 11:41:20 INFO  - Tracking order by number: 0000000032
2025-12-16 11:41:20 INFO  - Fetching order details for order: 0000000032
```

### **Backend Response (Error ❌)**
```
2025-12-16 11:41:20 ERROR - HTTP Error: 400 - {
  "message": "Yêu cầu đăng nhập để track order",
  "error": "Bad Request",
  "statusCode": 400
}
```

### **Frontend Logs (JWT Valid ✅)**
```javascript
[ChatStore] Session: {
  "customer_id": 1,
  "user_jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Im5ibWluaDI0QGdtYWlsLmNvbSIsInN1YiI6MSwiaWF0IjoxNzY1ODU5NzUxLCJleHAiOjE3NjU4NjA2NTF9.zK53iR9lcfRKlmSq5EIPkt0RMlQPdLoHWEVFpvNRRuU"
}

// JWT decoded:
{
  "email": "nbminh24@gmail.com",
  "sub": 1,  // customer_id
  "iat": 1765859751,
  "exp": 1765860651  // Valid until 11:50 (current time: 11:41)
}
```

---

## 🔎 Root Cause Analysis

### **Possible Causes**

#### **1. Endpoint Requires Different Authentication Method ❌**
Backend `/orders/track` might be using:
- `@UseGuards(AuthGuard)` - Requires JWT (should work)
- `@UseGuards(ApiKeyGuard)` - Requires API key instead of JWT
- No guard - Public endpoint (shouldn't require login)

#### **2. JWT Extraction Issue ❌**
Backend might be:
- Not reading `Authorization: Bearer <token>` header
- Expecting token in different header (e.g., `x-auth-token`)
- Expecting token in query params or cookies

#### **3. JWT Validation Failing ❌**
- Wrong JWT secret key
- Token signature verification failing
- Token expired (but logs show it's valid)

#### **4. Middleware Order Issue ❌**
Authentication middleware might not be running before the endpoint handler.

---

## 🧪 Diagnostic Tests

### **Test 1: Direct API Call with JWT**
```bash
# Test with valid JWT token
curl -X GET "http://localhost:3001/orders/track?order_id=0000000032" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Im5ibWluaDI0QGdtYWlsLmNvbSIsInN1YiI6MSwiaWF0IjoxNzY1ODU5NzUxLCJleHAiOjE3NjU4NjA2NTF9.zK53iR9lcfRKlmSq5EIPkt0RMlQPdLoHWEVFpvNRRuU" \
  -v

# Expected: 200 OK with order details
# Actual: 400 Bad Request "Yêu cầu đăng nhập"
```

### **Test 2: Check Endpoint Guard Configuration**
**File:** `backend/src/controllers/order.controller.ts` or `backend/src/routes/orders.routes.ts`

```typescript
// Current implementation (INCORRECT?)
@Get('/track')
@UseGuards(???)  // ← What guard is here?
async trackOrder(
  @Query('order_id') order_id: string,
  @Req() req: Request
) {
  // Check if req.user exists
  console.log('req.user:', req.user);  // ← Probably undefined
  
  if (!req.user) {
    throw new BadRequestException('Yêu cầu đăng nhập để track order');
  }
  
  // ...
}
```

**Problem:** Endpoint might be checking `req.user` without having an auth guard that populates it.

---

## ✅ Required Fix

### **Option 1: Add Auth Guard to Endpoint (If Missing)**

**File:** `backend/src/controllers/order.controller.ts`

```typescript
import { Controller, Get, Query, UseGuards, Req } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';  // or your custom auth guard

@Controller('orders')
export class OrderController {
  
  @Get('/track')
  @UseGuards(AuthGuard('jwt'))  // ✅ Add this guard
  async trackOrder(
    @Query('order_id') order_id: string,
    @Req() req: Request
  ) {
    const customer_id = req.user?.id;  // Now req.user will be populated
    
    if (!customer_id) {
      throw new UnauthorizedException('Authentication required');
    }
    
    const order = await this.orderService.findByOrderNumber(order_id);
    
    if (!order) {
      throw new NotFoundException('Không tìm thấy đơn hàng');
    }
    
    // Verify ownership
    if (order.customer_id !== customer_id) {
      throw new ForbiddenException('Bạn không có quyền xem đơn hàng này');
    }
    
    return {
      success: true,
      data: order
    };
  }
}
```

---

### **Option 2: Fix Auth Guard Strategy (If Exists But Broken)**

**File:** `backend/src/auth/jwt.strategy.ts`

```typescript
import { Injectable } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor() {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),  // ✅ Correct
      ignoreExpiration: false,
      secretOrKey: process.env.JWT_SECRET,  // ✅ Must match secret used to sign
    });
  }

  async validate(payload: any) {
    // This populates req.user
    return { 
      id: payload.sub,  // ✅ Customer ID from JWT
      email: payload.email 
    };
  }
}
```

**Check:**
```bash
# Verify JWT_SECRET matches
cat backend/.env | grep JWT_SECRET
```

---

### **Option 3: Make Endpoint Public (Not Recommended)**

If order tracking should be public (anyone with order number can track):

```typescript
@Get('/track')
@Public()  // Decorator to skip auth
async trackOrder(@Query('order_id') order_id: string) {
  // No authentication required
  const order = await this.orderService.findByOrderNumber(order_id);
  
  if (!order) {
    throw new NotFoundException('Không tìm thấy đơn hàng');
  }
  
  return { success: true, data: order };
}
```

**Not recommended** due to security issues (anyone can track any order).

---

## 🔍 Debugging Steps

### **Step 1: Check Backend Logs**
```bash
# Start backend with debug logging
npm run start:dev

# Look for:
# - "JWT Strategy initialized"
# - "Auth guard executed"
# - "req.user: undefined" or "req.user: { id: 1, email: ... }"
```

### **Step 2: Verify Auth Module Configuration**

**File:** `backend/src/app.module.ts`

```typescript
@Module({
  imports: [
    // ✅ Verify JwtModule is configured
    JwtModule.register({
      secret: process.env.JWT_SECRET,
      signOptions: { expiresIn: '15m' },
    }),
    
    // ✅ Verify PassportModule is imported
    PassportModule,
  ],
  providers: [
    // ✅ Verify JwtStrategy is provided
    JwtStrategy,
  ],
})
export class AppModule {}
```

### **Step 3: Test JWT Validation**

Create a test endpoint to verify JWT parsing:

```typescript
@Get('/test-auth')
@UseGuards(AuthGuard('jwt'))
async testAuth(@Req() req: Request) {
  return {
    success: true,
    user: req.user,
    message: 'JWT authentication working'
  };
}
```

**Test:**
```bash
curl "http://localhost:3001/test-auth" \
  -H "Authorization: Bearer <jwt_token>"

# Expected: { success: true, user: { id: 1, email: "..." } }
```

---

## 📊 Expected vs Actual

| Step | Expected | Actual | Status |
|------|----------|--------|---------|
| Chatbot extracts JWT | ✅ Token extracted | ✅ Token extracted | ✅ PASS |
| Chatbot sends JWT | ✅ `Authorization: Bearer ...` | ✅ `Authorization: Bearer ...` | ✅ PASS |
| Backend receives JWT | ✅ Token in header | ✅ Token in header | ✅ PASS |
| Backend validates JWT | ✅ `req.user` populated | ❌ `req.user` undefined | ❌ **FAIL** |
| Backend returns order | ✅ 200 OK | ❌ 400 Bad Request | ❌ **FAIL** |

---

## 🚨 Critical Questions for Backend Team

1. **Does `/orders/track` have `@UseGuards(AuthGuard('jwt'))`?**
   - If NO → Add the guard
   - If YES → Check why guard is not working

2. **Is `JwtStrategy` properly configured?**
   - Check `JWT_SECRET` in `.env`
   - Check `jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken()`

3. **Is `req.user` being populated?**
   - Add `console.log('req.user:', req.user)` in endpoint
   - If undefined → Auth guard not running or failing

4. **What error message does backend actually expect?**
   - Current: "Yêu cầu đăng nhập để track order"
   - This suggests manual check in controller, not guard failure

---

## 🔧 Temporary Workaround

**Chatbot Side:** Try alternative endpoints

```python
# Instead of /orders/track
# Try /orders with customer_id filter
def get_order_details_alt(self, order_id: str, auth_token: str):
    # Get all user orders
    result = self._make_request(
        "GET",
        "/orders",  # Authenticated endpoint
        auth_token=auth_token
    )
    
    # Filter for specific order
    if result.get("data"):
        for order in result["data"]:
            if order.get("order_number") == order_id:
                return {"data": order}
    
    return {"error": "Order not found"}
```

---

## ✅ Acceptance Criteria

- [ ] `/orders/track?order_id=X` with valid JWT returns 200 OK
- [ ] Response includes order details
- [ ] Invalid JWT returns 401 Unauthorized (not 400 Bad Request)
- [ ] Missing JWT returns 401 Unauthorized
- [ ] Chatbot can successfully track orders
- [ ] Backend logs show `req.user` is populated

---

## 📌 Priority

**CRITICAL** because:
1. Completely blocks order tracking feature
2. JWT authentication is fundamental
3. Simple configuration fix
4. Affects all authenticated endpoints

---

## 👨‍💻 Assigned To
**Backend Team - Authentication Module**

**Required:**
- Check auth guard configuration
- Verify JWT strategy
- Test with Postman/curl
- Fix and deploy

---

**NOTE:** Added debug logging to chatbot `api_client.py` to show:
- JWT token being sent (first 20 chars)
- Request URL and params
- Response status and body

Restart chatbot action server to see detailed logs:
```bash
rasa run actions
```

---

**END OF BUG REPORT**
