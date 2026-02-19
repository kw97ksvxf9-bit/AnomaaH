# Rating & Review System Implementation (Task 7)

## Overview

The Rating & Review System enables post-delivery feedback collection, rider reputation building, and quality metrics aggregation. Merchants can rate riders after successful deliveries, and the system tracks rider reputation across multiple dimensions.

**Features:**
- ✅ Post-delivery review creation with validation
- ✅ Rating aggregation and reputation scoring
- ✅ Review filtering (positive/neutral/negative)
- ✅ Time-based trends (weekly, monthly, all-time)
- ✅ Admin moderation and flagging
- ✅ Pagination and search
- ✅ Anonymous reviews support
- ✅ Platform-wide analytics

---

## Architecture

### Service Structure

```
/services/review_service/
├── main.py                 # FastAPI app with all endpoints
├── requirements.txt        # Dependencies
└── README.md              # Service documentation
```

### Database Models

**RiderReview Model** (existing in `/shared/models.py`):
```python
class RiderReview(Base):
    __tablename__ = "rider_reviews"
    
    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("orders.id"))
    rider_id = Column(String, ForeignKey("riders.id"))
    reviewer_id = Column(String, ForeignKey("users.id"))
    rating = Column(Integer)  # 1-5
    comment = Column(String, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(String, nullable=True)
    flagged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime)
```

### Data Flow

```
Merchant creates review for delivered order
    ↓
Review service validates order status (DELIVERED)
    ↓
Creates RiderReview record in PostgreSQL
    ↓
Aggregation engine calculates rider ratings
    ↓
Ratings visible in rider profile & assignment engine
```

---

## API Endpoints

### 1. Create Review

**POST** `/reviews/create`

Create a review for a delivered order.

**Request:**
```json
{
  "order_id": "ORD-12345",
  "rating": 5,
  "comment": "Excellent delivery, rider was friendly and professional",
  "is_anonymous": false
}
```

**Response (201):**
```json
{
  "id": "REV-001",
  "order_id": "ORD-12345",
  "rider_id": "RIDER-789",
  "rating": 5,
  "comment": "Excellent delivery, rider was friendly and professional",
  "is_anonymous": false,
  "created_at": "2024-01-15T10:30:00Z",
  "helpful_count": 0
}
```

**Errors:**
- `404 Not Found`: Order doesn't exist
- `400 Bad Request`: Order not DELIVERED or already reviewed
- `403 Forbidden`: Not order creator
- `422 Unprocessable Entity`: Invalid rating (must be 1-5)

**Validation Rules:**
- Rating: 1-5 (integer)
- Comment: Optional, max 500 chars, min 5 chars if provided
- Order must be in DELIVERED status
- Only merchant/customer who placed order can review
- Cannot review same order twice

---

### 2. Get Rider Rating Summary

**GET** `/riders/{rider_id}/rating`

Get overall rating information for a rider.

**Query Parameters:**
- `recent_limit` (optional, default=5): Number of recent reviews to include (1-20)

**Response (200):**
```json
{
  "rider_id": "RIDER-789",
  "rider_name": "Ahmed Hassan",
  "average_rating": 4.72,
  "total_reviews": 25,
  "rating_breakdown": {
    "1": 0,
    "2": 1,
    "3": 1,
    "4": 5,
    "5": 18
  },
  "recent_reviews": [
    {
      "id": "REV-025",
      "order_id": "ORD-15000",
      "rider_id": "RIDER-789",
      "rating": 5,
      "comment": "Perfect delivery",
      "is_anonymous": false,
      "created_at": "2024-01-15T10:30:00Z",
      "helpful_count": 2
    }
  ]
}
```

**Errors:**
- `404 Not Found`: Rider doesn't exist

---

### 3. Get Rider Detailed Stats

**GET** `/riders/{rider_id}/rating/stats`

Get comprehensive rider performance metrics.

**Response (200):**
```json
{
  "rider_id": "RIDER-789",
  "rider_name": "Ahmed Hassan",
  "average_rating": 4.72,
  "total_reviews": 25,
  "rating_trend": {
    "week": 4.85,
    "month": 4.78,
    "all_time": 4.72
  },
  "completion_rate": 98.5,
  "response_time_avg_min": 2.3,
  "delivery_speed_avg_min": 18.5
}
```

**Metrics:**
- `completion_rate`: % of assigned orders delivered successfully
- `response_time_avg_min`: Average time from assignment to pickup
- `delivery_speed_avg_min`: Average time from pickup to delivery
- `rating_trend`: Historical rating evolution

---

### 4. List Rider Reviews

**GET** `/riders/{rider_id}/reviews`

List all reviews for a rider with pagination and filtering.

**Query Parameters:**
- `page` (default=1): Page number
- `per_page` (default=10): Reviews per page (1-50)
- `filter` (default='all'): Filter type - `all`, `positive` (4-5), `neutral` (3), `negative` (1-2)

**Response (200):**
```json
{
  "reviews": [
    {
      "id": "REV-025",
      "order_id": "ORD-15000",
      "rider_id": "RIDER-789",
      "rating": 5,
      "comment": "Perfect delivery",
      "is_anonymous": false,
      "created_at": "2024-01-15T10:30:00Z",
      "helpful_count": 2
    }
  ],
  "total": 25,
  "page": 1,
  "per_page": 10,
  "pages": 3
}
```

---

### 5. Get Single Review

**GET** `/reviews/{review_id}`

Get details of a specific review.

**Response (200):**
```json
{
  "id": "REV-025",
  "order_id": "ORD-15000",
  "rider_id": "RIDER-789",
  "rating": 5,
  "comment": "Perfect delivery",
  "is_anonymous": false,
  "created_at": "2024-01-15T10:30:00Z",
  "helpful_count": 2
}
```

**Errors:**
- `404 Not Found`: Review doesn't exist

---

### 6. Delete Review

**DELETE** `/reviews/{review_id}`

Delete a review (reviewer or admin only).

**Response (200):**
```json
{
  "ok": true,
  "message": "Review deleted"
}
```

**Errors:**
- `404 Not Found`: Review doesn't exist
- `403 Forbidden`: Not reviewer or admin

---

### 7. Admin: List All Reviews

**GET** `/admin/reviews`

List all reviews platform-wide (admin only).

**Query Parameters:**
- `page` (default=1): Page number
- `per_page` (default=20): Reviews per page (1-100)
- `rider_id` (optional): Filter by rider
- `min_rating` (optional): Filter reviews >= rating (1-5)

**Response (200):**
```json
{
  "reviews": [
    {
      "id": "REV-025",
      "order_id": "ORD-15000",
      "rider_id": "RIDER-789",
      "reviewer_id": "MERCHANT-001",
      "rating": 5,
      "comment": "Perfect delivery",
      "is_anonymous": false,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1250,
  "page": 1,
  "per_page": 20,
  "pages": 63
}
```

---

### 8. Admin: Flag Review for Moderation

**POST** `/admin/reviews/{review_id}/flag`

Flag a review as inappropriate or suspicious.

**Request:**
```json
{
  "reason": "Offensive language"
}
```

**Response (200):**
```json
{
  "ok": true,
  "message": "Review flagged for review"
}
```

**Reasons:**
- "Offensive language"
- "Spam or promotional"
- "Unrelated to order"
- "Duplicate review"
- "Other"

---

### 9. Admin: Approve Flagged Review

**POST** `/admin/reviews/{review_id}/approve`

Clear a flagged review (approve it after moderation).

**Response (200):**
```json
{
  "ok": true,
  "message": "Review approved"
}
```

---

### 10. Platform Statistics

**GET** `/stats/ratings`

Get platform-wide rating analytics (requires authentication).

**Response (200):**
```json
{
  "total_reviews": 15230,
  "average_rating": 4.62,
  "distribution": {
    "1_star": 180,
    "2_star": 320,
    "3_star": 890,
    "4_star": 3450,
    "5_star": 10390
  },
  "top_riders": [
    {
      "rider_id": "RIDER-789",
      "average_rating": 4.95,
      "review_count": 85
    },
    {
      "rider_id": "RIDER-456",
      "average_rating": 4.88,
      "review_count": 72
    }
  ]
}
```

---

## Usage Examples

### Example 1: Create Review After Delivery

```bash
# Merchant creates review for completed order
curl -X POST http://localhost:8700/reviews/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD-12345",
    "rating": 5,
    "comment": "Excellent service, very professional"
  }'
```

### Example 2: Get Rider Rating

```bash
# View rider's overall rating
curl http://localhost:8700/riders/RIDER-789/rating?recent_limit=10
```

### Example 3: List Reviews with Filtering

```bash
# Get positive reviews (4-5 stars) for a rider
curl "http://localhost:8700/riders/RIDER-789/reviews?filter=positive&page=1&per_page=20"
```

### Example 4: View Rider Stats

```bash
# Get detailed performance metrics
curl http://localhost:8700/riders/RIDER-789/rating/stats
```

### Example 5: Admin Moderation

```bash
# Admin flags inappropriate review
curl -X POST http://localhost:8700/admin/reviews/REV-025/flag \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Offensive language"}'

# After review, approve the flagged review
curl -X POST http://localhost:8700/admin/reviews/REV-025/approve \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Example 6: Platform Analytics

```bash
# Get rating distribution and top performers
curl http://localhost:8700/stats/ratings \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Integration with Assignment Engine

The rating system integrates with the automatic rider assignment service (Task 6) to improve assignment quality:

```python
# Assignment scoring includes rider rating
# HIGHEST_RATING strategy prioritizes riders with 4.5+ average
# HYBRID strategy includes rating in multi-factor scoring

def score_rider(rider, order, strategy):
    if strategy == AssignmentStrategy.HIGHEST_RATING:
        return rider.average_rating  # 0-5 scale
    
    elif strategy == AssignmentStrategy.HYBRID:
        # Hybrid considers rating (30%) + proximity (40%) + load (20%) + speed (10%)
        rating_score = rider.average_rating / 5.0  # Normalize 0-1
        return 0.30 * rating_score + ...
```

This creates a virtuous cycle:
- **Good reviews → Higher ratings → More assignments → Higher revenue**
- **Poor reviews → Lower ratings → Fewer assignments → Motivation to improve**

---

## Admin Dashboard Integration

The review system data appears in the superadmin dashboard:

```html
<!-- Rider quality metrics section -->
<div class="rider-quality">
  <h3>Top Rated Riders</h3>
  <table>
    <tr>
      <th>Rider</th>
      <th>Rating</th>
      <th>Reviews</th>
      <th>Completion Rate</th>
    </tr>
    <tr>
      <td>Ahmed Hassan</td>
      <td>4.95 ⭐</td>
      <td>85 reviews</td>
      <td>98.5%</td>
    </tr>
  </table>
</div>

<!-- Moderation queue section -->
<div class="moderation">
  <h3>Flagged Reviews</h3>
  <!-- Links to /admin/reviews?flagged=true -->
</div>
```

---

## Security Considerations

### Input Validation
- Comments sanitized to prevent XSS
- Rating validated to 1-5 range
- Order ownership verified before review creation

### Authorization
- Only merchants/customers who placed order can review
- Admins can flag/moderate reviews
- Users can delete their own reviews

### Rate Limiting
- Inherited from `/shared/security.py`
- API endpoints protected with request limiting

### Constant-Time Operations
- Review deletion uses database-level cascade
- No timing attacks on review existence checks

---

## Performance Optimization

### Indexing
```python
# Recommended PostgreSQL indexes for performance:
CREATE INDEX idx_rider_reviews ON rider_reviews(rider_id);
CREATE INDEX idx_order_reviews ON rider_reviews(order_id);
CREATE INDEX idx_review_created ON rider_reviews(created_at DESC);
CREATE INDEX idx_review_rating ON rider_reviews(rating);
```

### Aggregation
- Average ratings cached per rider (can implement Redis caching)
- Weekly/monthly aggregations calculated on-demand
- Top riders query limited to top 5

### Pagination
- Default page size: 10 reviews
- Maximum page size: 50 reviews
- Total count included for UI pagination

---

## Testing

### Unit Tests

```python
def test_create_review_for_delivered_order():
    # Create order with DELIVERED status
    # Create review
    # Assert review created with correct data

def test_cannot_review_non_delivered_order():
    # Create order with PENDING status
    # Try to create review
    # Assert 400 error

def test_cannot_review_same_order_twice():
    # Create review for order
    # Try to create another review for same order
    # Assert 400 error

def test_only_order_creator_can_review():
    # Create review as non-creator
    # Assert 403 Forbidden

def test_rating_aggregation():
    # Create 10 reviews with ratings [5,5,5,5,4,4,4,3,3,3]
    # Get rider rating
    # Assert average = 4.1

def test_review_filtering():
    # Create mixed reviews
    # Filter by positive (4-5)
    # Assert returns only high-rated reviews
```

### Integration Tests

```bash
# Test full flow
1. Create order
2. Update order status to DELIVERED
3. Create review
4. Get rider rating
5. Assert rating updated correctly
6. Admin flag review
7. Admin approve review
```

---

## Troubleshooting

### "Order not found"
- Verify order ID is correct
- Check order exists in database

### "Can only review delivered orders"
- Order must have status = DELIVERED
- Check order status in order_service
- Wait for delivery before reviewing

### "You have already reviewed this order"
- Each merchant can only review once per order
- Delete previous review first if needed

### "Only order creator can review"
- Only merchant/customer who placed order can review
- Verify using correct user token

### Low average ratings not affecting assignment
- Check assignment service is using rating in scoring
- Verify HIGHEST_RATING strategy is configured
- Check rider rating cache is updated

---

## Future Enhancements

1. **Rider Response to Reviews**
   - Allow riders to respond to negative reviews
   - Improve service based on feedback

2. **Review Photos/Videos**
   - Attach delivery proof photos
   - Video testimonials from satisfied customers

3. **Detailed Feedback**
   - Structured questions (politeness, speed, cleanliness)
   - Separate metrics for different aspects

4. **Reputation Recovery**
   - Temporary rating suspension for disputes
   - Dispute resolution system

5. **Incentive Program**
   - Reward high-rated riders with bonuses
   - Promote excellence program

6. **ML-Based Spam Detection**
   - Detect fake reviews
   - Flag suspicious patterns
   - Sentiment analysis on comments

7. **Customer Support**
   - Link support tickets to negative reviews
   - Follow-up mechanism

---

## Deployment

### Prerequisites
- PostgreSQL with RiderReview table
- FastAPI 0.68+
- SQLAlchemy 1.4+
- Pydantic 1.8+

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/delivery_db
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
```

### Running the Service
```bash
cd services/review_service
pip install -r requirements.txt
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8700 --reload
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8700"]
```

---

## Summary

The Rating & Review System provides comprehensive post-delivery feedback collection with aggregation, filtering, and moderation capabilities. Integration with the assignment engine creates a quality-driven marketplace where excellent service is rewarded with more deliveries.

**Key Metrics:**
- ✅ 10 API endpoints for review management
- ✅ Rating aggregation with time-based trends
- ✅ Admin moderation workflow
- ✅ Platform-wide analytics
- ✅ Pagination and filtering
- ✅ PostgreSQL persistence

**Next Task:** WebSocket support for real-time order tracking and notifications.
