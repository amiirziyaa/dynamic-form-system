# Testing Summary for Admin Reports and WebSocket Updates

## Test Files Created

### 1. `notifications/test_admin_endpoints.py`
**Coverage**: Admin Reports and Webhooks endpoints

**Test Cases**:
- ✅ `test_list_webhooks_admin` - Admin can list webhooks
- ✅ `test_list_webhooks_unauthorized` - Regular users denied access
- ✅ `test_create_webhook` - Create new webhook
- ✅ `test_get_webhook_detail` - Get webhook details
- ✅ `test_update_webhook` - Update webhook
- ✅ `test_delete_webhook` - Delete webhook
- ✅ `test_test_webhook` - Test webhook endpoint
- ✅ `test_list_report_configs` - List report configurations
- ✅ `test_create_report_config` - Create report configuration
- ✅ `test_update_report_config` - Update report configuration
- ✅ `test_delete_report_config` - Delete report configuration
- ✅ `test_generate_manual_report` - Manual report generation
- ✅ `test_list_report_history` - List report history
- ✅ `test_download_report_completed` - Download completed report
- ✅ `test_download_report_pending` - Download pending report
- ✅ `test_unauthorized_access` - Non-admin users denied

**Total**: 15 test cases

### 2. `analytics/test_websocket.py`
**Coverage**: WebSocket consumer and real-time report REST endpoint

**Test Cases**:
- ✅ `test_consumer_class_exists` - Verify consumer has required methods
- ✅ `test_real_time_report_endpoint` - Real-time REST endpoint returns snapshot + WebSocket URL
- ✅ `test_real_time_report_unauthorized` - Requires authentication
- ✅ `test_real_time_report_non_owner` - Requires form ownership

**Total**: 4 test cases

**Note**: Full async WebSocket connection tests require:
- Daphne server running
- Channel layer configured (Redis)
- Async test framework setup

## Running Tests

### Prerequisites
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or your venv path

# Install dependencies (if not already installed)
pip install daphne channels channels-redis
```

### Run Admin Endpoints Tests
```bash
python manage.py test notifications.test_admin_endpoints --keepdb
```

### Run WebSocket Tests (REST endpoints only)
```bash
python manage.py test analytics.test_websocket --keepdb
```

### Run All New Tests
```bash
python manage.py test notifications.test_admin_endpoints analytics.test_websocket --keepdb
```

### Run All Tests
```bash
python manage.py test --keepdb
```

## Test Coverage

### Admin Reports Endpoints
- ✅ Webhook CRUD operations
- ✅ Webhook testing
- ✅ Report configuration CRUD
- ✅ Manual report generation
- ✅ Report history listing
- ✅ Report download
- ✅ Authorization checks (admin only)

### WebSocket Functionality
- ✅ Consumer class structure validation
- ✅ Real-time report REST endpoint
- ✅ Authentication requirements
- ✅ Ownership requirements

## Manual Testing

### Test WebSocket Connection (requires Daphne server)

1. **Start Daphne server**:
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

2. **Connect via WebSocket**:
```javascript
// JavaScript example
const ws = new WebSocket('ws://localhost:8000/ws/v1/forms/{form_slug}/reports/live/');
ws.onopen = () => {
    console.log('Connected');
    // Send ping
    ws.send(JSON.stringify({type: 'ping', timestamp: new Date().toISOString()}));
};
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

3. **Test REST endpoint**:
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/forms/{slug}/analytics/reports/real-time/
```

## Expected Test Results

All tests should pass when:
1. Database is properly configured
2. All dependencies are installed
3. Test database is set up

## Notes

- **Periodic Task Creation**: Report schedules with `is_active=True` automatically create Celery Beat periodic tasks. Tests set `is_active=False` to avoid this dependency.
- **WebSocket Testing**: Full WebSocket tests require async test framework and running Daphne server. Current tests focus on REST endpoints and consumer structure validation.
- **Channel Layer**: WebSocket functionality requires Redis or in-memory channel layer configured.

