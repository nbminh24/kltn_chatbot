# 🔧 BACKEND RASA INTEGRATION - IMPLEMENTATION CODE

**For Backend Team**  
**Date:** December 7, 2025  
**Purpose:** Fix bug - Integrate Rasa webhook into chat service

---

## 📋 OVERVIEW

Backend cần gọi Rasa server để xử lý NLU thay vì trả hardcoded responses.

---

## 🔧 STEP 1: UPDATE .ENV

**File:** `.env`

```env
# Rasa Configuration
RASA_URL=http://localhost:5005
RASA_WEBHOOK_PATH=/webhooks/rest/webhook
RASA_TIMEOUT=10000

# Gemini Fallback (nếu Rasa down)
GEMINI_API_KEY=your_gemini_key_here
```

---

## 🔧 STEP 2: CREATE RASA CLIENT SERVICE

**File:** `src/chat/rasa-client.service.ts` (NEW FILE)

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios, { AxiosInstance } from 'axios';

export interface RasaMessage {
  recipient_id: string;
  text: string;
  image?: string;
  buttons?: Array<{ title: string; payload: string }>;
  custom?: any;
}

export interface RasaWebhookRequest {
  sender: string;
  message: string;
  metadata?: any;
}

@Injectable()
export class RasaClientService {
  private readonly logger = new Logger(RasaClientService.name);
  private readonly rasaUrl: string;
  private readonly webhookPath: string;
  private readonly timeout: number;
  private readonly axiosInstance: AxiosInstance;

  constructor(private readonly configService: ConfigService) {
    this.rasaUrl = this.configService.get<string>('RASA_URL', 'http://localhost:5005');
    this.webhookPath = this.configService.get<string>('RASA_WEBHOOK_PATH', '/webhooks/rest/webhook');
    this.timeout = this.configService.get<number>('RASA_TIMEOUT', 10000);

    this.axiosInstance = axios.create({
      baseURL: this.rasaUrl,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.logger.log(`Rasa Client initialized: ${this.rasaUrl}${this.webhookPath}`);
  }

  /**
   * Send message to Rasa webhook and get responses
   */
  async sendMessage(
    message: string,
    senderId: string,
    metadata?: any,
  ): Promise<RasaMessage[]> {
    const requestData: RasaWebhookRequest = {
      sender: senderId,
      message: message,
      metadata: metadata,
    };

    try {
      this.logger.debug(`Sending to Rasa: ${JSON.stringify(requestData)}`);

      const response = await this.axiosInstance.post<RasaMessage[]>(
        this.webhookPath,
        requestData,
      );

      this.logger.debug(`Rasa response: ${JSON.stringify(response.data)}`);

      return response.data || [];
    } catch (error) {
      this.logger.error('Failed to call Rasa webhook:', error.message);
      
      // Return empty array on error (caller should handle fallback)
      return [];
    }
  }

  /**
   * Set slot value for a conversation
   */
  async setSlot(senderId: string, slotName: string, slotValue: any): Promise<void> {
    try {
      await this.axiosInstance.post(`/conversations/${senderId}/tracker/events`, {
        event: 'slot',
        name: slotName,
        value: slotValue,
      });

      this.logger.debug(`Set slot ${slotName}=${slotValue} for ${senderId}`);
    } catch (error) {
      this.logger.error(`Failed to set slot: ${error.message}`);
    }
  }

  /**
   * Get conversation tracker (for debugging)
   */
  async getTracker(senderId: string): Promise<any> {
    try {
      const response = await this.axiosInstance.get(`/conversations/${senderId}/tracker`);
      return response.data;
    } catch (error) {
      this.logger.error(`Failed to get tracker: ${error.message}`);
      return null;
    }
  }

  /**
   * Check if Rasa server is healthy
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.axiosInstance.get('/');
      return response.status === 200;
    } catch (error) {
      this.logger.error('Rasa health check failed:', error.message);
      return false;
    }
  }
}
```

---

## 🔧 STEP 3: UPDATE CHAT SERVICE

**File:** `src/chat/chat.service.ts`

### Import Rasa Client:

```typescript
import { RasaClientService, RasaMessage } from './rasa-client.service';
import { GeminiAiService } from '../gemini-ai/gemini-ai.service'; // Assuming you have this
```

### Inject Dependencies:

```typescript
constructor(
  @InjectRepository(ChatSession)
  private readonly sessionsRepository: Repository<ChatSession>,
  
  @InjectRepository(ChatMessage)
  private readonly messagesRepository: Repository<ChatMessage>,
  
  private readonly rasaClientService: RasaClientService,
  private readonly geminiAiService: GeminiAiService, // For fallback
) {}
```

### Update sendMessage Method:

```typescript
async sendMessage(dto: SendMessageDto): Promise<any> {
  const { session_id, message } = dto;

  // 1. Validate session
  const session = await this.sessionsRepository.findOne({
    where: { id: session_id },
    relations: ['customer'],
  });

  if (!session) {
    throw new NotFoundException(`Session ${session_id} not found`);
  }

  // 2. Save user message to database
  const userMessage = await this.messagesRepository.save({
    session_id: session_id,
    sender: 'customer',
    message: message,
    message_type: 'text',
    created_at: new Date(),
  });

  this.logger.log(`User message saved: ${message}`);

  // 3. Generate sender ID for Rasa (session or customer based)
  const senderId = session.customer_id 
    ? `customer_${session.customer_id}` 
    : `session_${session_id}`;

  // 4. Set customer_id slot if user is logged in
  if (session.customer_id) {
    await this.rasaClientService.setSlot(
      senderId,
      'customer_id',
      session.customer_id,
    );
  }

  // 5. Call Rasa webhook
  let rasaResponses: RasaMessage[] = [];
  
  try {
    rasaResponses = await this.rasaClientService.sendMessage(
      message,
      senderId,
      { session_id, customer_id: session.customer_id },
    );

    this.logger.log(`Rasa returned ${rasaResponses.length} responses`);
  } catch (error) {
    this.logger.error('Rasa call failed, using fallback', error);
  }

  // 6. Fallback to Gemini if Rasa returns nothing
  if (!rasaResponses || rasaResponses.length === 0) {
    this.logger.warn('Rasa returned empty, falling back to Gemini AI');
    
    const geminiResponse = await this.geminiAiService.askQuestion(message);
    
    rasaResponses = [{
      recipient_id: senderId,
      text: geminiResponse || 'Xin lỗi, mình không hiểu câu hỏi này. Bạn có thể hỏi lại được không?',
      custom: { source: 'gemini_fallback' },
    }];
  }

  // 7. Save bot responses to database
  const botMessages = [];
  
  for (const rasaMsg of rasaResponses) {
    const savedBotMsg = await this.messagesRepository.save({
      session_id: session_id,
      sender: 'bot',
      message: rasaMsg.text,
      message_type: this.detectMessageType(rasaMsg),
      custom_data: rasaMsg.custom || null,
      created_at: new Date(),
    });

    botMessages.push(savedBotMsg);
  }

  this.logger.log(`Saved ${botMessages.length} bot responses`);

  // 8. Return formatted response
  return {
    customer_message: userMessage,
    bot_responses: botMessages,
  };
}

/**
 * Detect message type from Rasa response
 */
private detectMessageType(rasaMsg: RasaMessage): string {
  if (rasaMsg.image) return 'image';
  if (rasaMsg.buttons && rasaMsg.buttons.length > 0) return 'quick_reply';
  if (rasaMsg.custom?.products) return 'product_card';
  if (rasaMsg.custom?.order) return 'order_card';
  return 'text';
}
```

---

## 🔧 STEP 4: UPDATE CHAT MODULE

**File:** `src/chat/chat.module.ts`

```typescript
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ChatController } from './chat.controller';
import { ChatService } from './chat.service';
import { RasaClientService } from './rasa-client.service';
import { ChatSession } from './entities/chat-session.entity';
import { ChatMessage } from './entities/chat-message.entity';
import { GeminiAiModule } from '../gemini-ai/gemini-ai.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([ChatSession, ChatMessage]),
    GeminiAiModule, // For fallback
  ],
  controllers: [ChatController],
  providers: [
    ChatService,
    RasaClientService, // ADD THIS
  ],
  exports: [ChatService, RasaClientService],
})
export class ChatModule {}
```

---

## 🔧 STEP 5: ADD HEALTH CHECK ENDPOINT

**File:** `src/chat/chat.controller.ts`

```typescript
@Get('health/rasa')
async checkRasaHealth() {
  const isHealthy = await this.rasaClientService.healthCheck();
  
  return {
    rasa_status: isHealthy ? 'healthy' : 'unhealthy',
    rasa_url: process.env.RASA_URL,
    timestamp: new Date().toISOString(),
  };
}
```

---

## 🧪 TESTING

### Test 1: Check Rasa Health

```bash
GET http://localhost:3001/chat/health/rasa
```

**Expected:**
```json
{
  "rasa_status": "healthy",
  "rasa_url": "http://localhost:5005",
  "timestamp": "2024-12-07T10:00:00.000Z"
}
```

### Test 2: Send Message

```bash
POST http://localhost:3001/chat/send
Content-Type: application/json

{
  "session_id": 1,
  "message": "Chào shop"
}
```

**Expected:**
```json
{
  "customer_message": {
    "id": 123,
    "message": "Chào shop",
    "sender": "customer",
    ...
  },
  "bot_responses": [
    {
      "id": 124,
      "message": "Chào bạn! 👋 Mình là trợ lý ảo...",
      "sender": "bot",
      "custom_data": null,
      ...
    }
  ]
}
```

### Test 3: Product Search

```bash
POST http://localhost:3001/chat/send

{
  "session_id": 1,
  "message": "Tìm áo thun đen"
}
```

**Expected:** Bot response with product cards (custom_data includes products)

---

## 🚨 ERROR HANDLING

### If Rasa is down:

1. Log error
2. Fall back to Gemini AI
3. Return generic response if both fail

### If Rasa returns error:

1. Catch exception
2. Log for debugging
3. Try Gemini fallback
4. Return user-friendly message

---

## ✅ CHECKLIST

**Before Deployment:**

- [ ] `.env` has `RASA_URL` configured
- [ ] Rasa server is running on specified URL
- [ ] Rasa health check returns 200
- [ ] Test basic greeting intent
- [ ] Test product search intent
- [ ] Test size consultation
- [ ] Verify custom_data is saved correctly
- [ ] Test fallback when Rasa is down
- [ ] Check database logs for bot responses

---

## 📊 EXPECTED RESULTS

### After Fix:

✅ Backend calls Rasa for every message  
✅ NLU processing happens  
✅ 29 intents work  
✅ Custom actions execute  
✅ Internal APIs get called  
✅ Slot filling works  
✅ Gemini fallback works  

---

## 🔗 RELATED FILES

**Backend needs:**
- `src/chat/rasa-client.service.ts` (NEW - create this)
- `src/chat/chat.service.ts` (UPDATE - modify sendMessage)
- `src/chat/chat.module.ts` (UPDATE - add RasaClientService)
- `src/chat/chat.controller.ts` (UPDATE - add health check)
- `.env` (UPDATE - add RASA_URL)

**Rasa side (already done):**
- ✅ Actions implemented
- ✅ Domain configured
- ✅ API client ready
- ✅ All endpoints working

---

**Implementation Code v1.0**  
**Ready to use - Copy & Paste**  
**Estimated time:** 30 minutes
