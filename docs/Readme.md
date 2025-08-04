# Smart Notification System

**A comprehensive, scalable notification system with:**

* ✅ Multi-channel delivery (In-app, Email, SMS)
* ✅ Dynamic event types (no code deployment needed)
* ✅ User preference management
* ✅ Async processing with retry logic
* ✅ Comprehensive delivery tracking

---

## 2. System Architecture 

### High-Level Architecture

```

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Django API    │    │   Background    │
│                 │    │                 │    │                 │
│ • React UI      │◄──►│ • REST APIs     │◄──►│ • Celery Tasks  │
│ • Real-time     │    │ • Business      │    │ • Redis Queue   │
│ • Preferences   │    │   Logic         │    │ • Delivery      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Database      │
                       │                 │
                       │ • PostgreSQL    │
                       │ • Optimized     │
                       │ • Indexed       │
                       └─────────────────┘
```

### Microservice ready architecture

* Seperation of concern (service layer, backend layer, api layer, queue system)
* Testability
* Maintainability
* Event driven Design

### Database Schema

```sql
-- Core Models
EventType {
    id: PK
    code: VARCHAR(50) UNIQUE    -- "new_comment", "login_alert"
    name: VARCHAR(100)          -- "New Comment", "Login Alert"
    description: TEXT
    default_enabled: BOOLEAN
    is_active: BOOLEAN
}

User {
    id: PK
    username: VARCHAR
    email: VARCHAR
    created_at: TIMESTAMP
}

-- Notification Instance
Notification {
    id: PK
    user_id: FK → User
    event_type_id: FK → EventType
    title: VARCHAR(200)
    message: TEXT
    metadata: JSON              -- Dynamic context data
    is_read: BOOLEAN
    read_at: TIMESTAMP
    created_at: TIMESTAMP
}

-- User Preferences
NotificationPreference {
    id: PK
    user_id: FK → User (UNIQUE)
    in_app_enabled: BOOLEAN
    email_enabled: BOOLEAN
    sms_enabled: BOOLEAN
}

UserEventPreference {
    id: PK
    user_id: FK → User
    event_type_id: FK → EventType
    is_enabled: BOOLEAN
    UNIQUE(user_id, event_type_id)
}

-- Delivery Tracking
NotificationDelivery {
    id: PK
    notification_id: FK → Notification
    channel: VARCHAR(20)        -- "email", "sms", "in_app"
    status: VARCHAR(20)         -- "pending", "sent", "failed"
    attempted_at: TIMESTAMP
    delivered_at: TIMESTAMP
    retry_count: INTEGER
    error_message: TEXT
}
```

### Key Design Decisions

#### 1. **EventType as First-Class Entity**

```python
# Instead of hardcoded enums
class EventType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    # ... other fields
```

**Why?** Enables runtime creation of new notification types without code deployment.

#### 2. **Separate Delivery Tracking**

```python
class NotificationDelivery(models.Model):
    notification = models.ForeignKey(Notification)
    channel = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    retry_count = models.IntegerField(default=0)
```

**Why?** Track delivery success/failure per channel, enable retry logic.

#### 3. **Service Layer Architecture**

```python
class NotificationService:
    @classmethod
    def dispatch_notification(cls, event_type_code, context, target_users):
        # Single responsibility: handle business logic
        # Reusable across views, signals, and tasks
	# Validate Event Type
	# Fond Target Userrs
	# Check user Preference
	# Get Template
	# Create Notification
	# Track Notification Status
	# Deliver Notification(retry=3)
	# Queue Delivery
```

**Why?** Clean separation of concerns, testable, reusable.

#### 4. Backend Abstraction

**Why?** Polymorphism, Extensibility, Mock Testing

---

## 3. Demo

#### Scenario 1: User Registration # 1. Create User

* Signal automatically creates preferences
* Default event types created

#### Scenario 2: User Login

* Create User
* signal automatically create device info
* unrecognized device detection

#### **Scenario 3: Dynamic Event Creation**

* Runtime event creation (api )
* Immediate availability for use
* Template auto-generation

#### **Scenario 3: Comment Notification**

* Automatic signal triggering
* Async Celery processing
* Multi-user notification creation

#### **Scenario 4: Preference Management**

* Granular preference control
* Immediate effect on notifications
* User empowerment

#### **Scenario 5: Weekly Summary**

* Celery Beat

---

## 4. Technical Deep Dive

### Async Processing Flow

```python
# 1. Signal Triggered
@receiver(post_save, sender=Comment)
def notify_on_new_comment(sender, instance, created, **kwargs):
    if created:
        NotificationService.dispatch_notification(
            event_type_code="new_comment",
            context={"post_title": instance.post.title},
            target_users=get_related_user_ids(instance.post)
        )

# 2. Service Layer Processing
def dispatch_notification(cls, event_type_code, context, target_users):
    for user_id in target_users:
        notification = cls.create_notification(user, event_type_code, context)
        # Queue delivery tasks
        for channel in user.get_enabled_channels():
            deliver_notification_task.delay(notification.id, channel)

# 3. Celery Task Execution
@shared_task(bind=True, max_retries=3)
def deliver_notification_task(self, notification_id, channel):
    try:
        backend = get_notification_backend(channel)
        success = backend.send_notification(notification)
        # Update delivery status
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2**retry_count))
```

### Backend Abstraction

```python
class NotificationBackend(ABC):
    @abstractmethod
    def send_notification(self, notification) -> bool:
        pass

class EmailBackend(NotificationBackend):
    def send_notification(self, notification) -> bool:
        # Django email integration
        send_mail(
            subject=notification.title,
            message=notification.message,
            recipient_list=[notification.user.email]
        )

class SMSBackend(NotificationBackend):
    def send_notification(self, notification) -> bool:
        # Twilio/AWS SNS integration
        # send_sms(phone, message)
```

### Performance Optimizations

* **Database Indexes** : `user_id`, `event_type_id`, `created_at`
* **Query Optimization** : `select_related()`, `prefetch_related()`
* **Bulk Operations** : `bulk_create()` for batch processing
* **Caching** : Redis for user preferences and templates
* **Pagination**
* **Backend Filter**
* **Asynchtonous Processing**

---

## 5. Scalability & Future

### Scaling Strategy

```
Current: Single Server
    ↓
Horizontal Scaling:
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ API Server  │  │ API Server  │  │ API Server  │
│   Node 1    │  │   Node 2    │  │   Node N    │
└─────────────┘  └─────────────┘  └─────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
            ┌─────────────────┐
            │ Shared Services │
            │ • Redis Cluster │
            │ • PostgreSQL    │
            │ • Load Balancer │
            └─────────────────┘
```

### Future Roadmap

* **WebSocket Integration** : Django Channels for real-time notifications
* **Push Notifications** : FCM/APNS for mobile apps
* **Real-time Dashboard** : Live notification monitoring
* **Advanced Integrations** : Slack, Teams, Discord channels
* **Message Queuing** : Migrate from Redis to RabbitMQ/AWS SQS for enterprise scale
* **Database** : Shard notifications table by user_id for massive scale
* **Caching** : Redis cluster for distributed caching
* **Monitoring** : Prometheus + Grafana for metrics and alerting

#### **Enterprise**

* **Multi-Tenant** : Support multiple organizations
* **Compliance** : GDPR, audit trails, data retention policies
