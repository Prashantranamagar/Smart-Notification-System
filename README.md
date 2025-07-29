# Smart Notification System

A comprehensive Django REST API-based notification system with intelligent event handling, user preferences, and multi-channel delivery support. The system includes a complete post and comment functionality with automatic notification triggers for user engagement.

## 🚀 Features

- **Dynamic Event Management**: Create and manage notification event types dynamically
- **Multi-Channel Delivery**: Support for in-app, email, and SMS notifications
- **Smart User Preferences**: Granular control over notification preferences per event type
- **Automatic Triggers**: Smart notifications for post interactions (comments, likes, mentions)
- **Delivery Tracking**: Complete notification delivery status and retry mechanisms
- **RESTful API**: Well-documented API endpoints with proper pagination and filtering
- **Real-time Notifications**: Support for real-time notification delivery
- **Bulk Operations**: Efficient bulk notification management

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Authentication](#authentication)
- [API Documentation](#api-documentation)
- [Design Decisions](#design-decisions)


## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Django 4.2+
- PostgreSQL 12+ (recommended) or SQLite (development)
- Redis (for Celery background tasks)

### Setup Instructions

1. **Clone the repository**
```bash
git clone https://github.com/Prashantranamagar/Smart-Notification-System.git
cd smart-notification-system
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Database Setup**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

6. **Load Initial Data**
```bash
python manage.py create_default_event_types
python manage.py create_default_notification_template

```

7. **Start the development server**
```bash
python manage.py runserver
```



## 🗄️ Database Setup

### PostgreSQL (Recommended for Production)

### SQLite (Development Only)

For development, you can use SQLite by setting:
```env
DATABASE_URL=sqlite:///db.sqlite3
```
### Set up Redis 

On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

Using Docker
```bash
docker run -d -p 6379:6379 redis
```

.8 **Start the celery worker and celery beat**
```bash
 celery -A notification worker --loglevel=info
 celery -A notification beat --loglevel=info
```


## 🔐 Authentication

The system uses **JWT (JSON Web Tokens)** for authentication with the following endpoints:


### JWT Token Usage

Include the JWT token in the Authorization header:
```bash
Authorization: Bearer <your_access_token>
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1/
```

## Documentation URLs

| Type           | Endpoint      | Description                   |
|----------------|---------------|-------------------------------|
| Swagger UI     | `/docs/`      | Interactive API documentation |
| ReDoc          | `/redoc/`     | Alternative API docs viewer   |
| OpenAPI Schema | `/schema/`    | JSON schema for Swagger/OpenAPI |



> You can use the OpenAPI schema with Postman or SwaggerHub for testing or sharing APIs.


## 🏗️ Design Decisions

### 1. **Event-Driven Architecture**
- **Decision**: Implemented an event-driven notification system where actions trigger specific events
- **Reason**: Provides flexibility to add new notification types without modifying core logic
- **Benefits**: Scalable, maintainable, and easily extensible

### 2. **Dynamic Event Type Management**
- **Decision**: Event types are stored in database rather than hardcoded
- **Reason**: Allows runtime configuration and easy addition of new notification types
- **Implementation**: Admin interface for managing event types with automatic user preference creation

### 3. **Multi-Channel Delivery Strategy**
- **Decision**: Separate delivery tracking for each notification channel
- **Reason**: Different channels have different reliability and timing requirements
- **Implementation**: `NotificationDelivery` model tracks status per channel with retry mechanisms

### 4. **User Preference Granularity**
- **Decision**: Two-level preference system (global channels + per-event-type preferences)
- **Reason**: Provides fine-grained control while maintaining simplicity
- **Benefits**: Users can disable email globally but still receive critical notifications

### 5. **Smart Notification Context**
- **Decision**: Rich context data stored as JSON in notifications
- **Reason**: Enables personalized notification templates and rich client-side rendering
- **Implementation**: Template-based message generation with dynamic context injection

### 6. **Automatic Relationship Detection**
- **Decision**: System automatically determines who should receive notifications
- **Reason**: Reduces manual work and ensures relevant users are notified
- **Examples**: Comment notifications go to post author, other commenters, and mentioned users

### 7. **Bulk Operations Support**
- **Decision**: Support for bulk notification operations (mark as read, preferences update)
- **Reason**: Better user experience and reduced API calls
- **Implementation**: Validated bulk serializers with transaction support

### 8. **Delivery Status Tracking**
- **Decision**: Comprehensive tracking of notification delivery attempts
- **Reason**: Enables debugging, analytics, and retry logic
- **Data Tracked**: Attempt time, delivery time, failure reasons, retry count

### 9. **Scalability Considerations**
- **Decision**: Asynchronous notification processing with Celery
- **Reason**: Prevents blocking API responses during bulk notifications
- **Implementation**: Background tasks for email/SMS delivery with proper error handling


### 10. API Design & Performance
- **Pagination**: Limits response size for better performance and UX
- **Filtering**: Flexible data querying with DjangoFilterBackend and search/order filters

### 10. **Security and Privacy**
- **Decision**: Secure user-specific data access with rate limiting
- **Reason**: Ensure data privacy, prevent abuse, and restrict unauthorized access
- **Implementation**: 
  - JWT Authentication (`SimpleJWT`)
  - IsAuthenticated permission
  - QuerySet filtering to return only the user's data
  - Throttling: 100/hour (user), 10/minute (anonymous)
