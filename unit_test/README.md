# 🧪 Unit Tests & Development Tools

This folder contains development and testing utilities for the Google ADK No-Code Platform.

## 📁 Files

### `check_db.py`
Database connection and schema verification utility.
- Tests database connectivity
- Verifies table structures
- Checks data integrity

### `test_platform.py`
Platform functionality testing script.
- Tests API endpoints
- Verifies agent and tool operations
- Validates AI suggestion functionality

### `start_platform.py`
Platform startup and configuration testing.
- Tests platform initialization
- Verifies service dependencies
- Checks configuration loading

### `add_updated_at.py`
Database migration utility.
- Adds `updated_at` timestamp columns
- Updates existing records
- Maintains data consistency

## 🚀 Usage

### Running Tests
```bash
# Test database connectivity
python unit_test/check_db.py

# Test platform functionality
python unit_test/test_platform.py

# Test platform startup
python unit_test/start_platform.py

# Run database migration
python unit_test/add_updated_at.py
```

### Development Workflow
1. **Before making changes**: Run relevant tests
2. **After changes**: Verify functionality with tests
3. **Before deployment**: Run full test suite

## 📋 Test Categories

### Unit Tests
- Individual component testing
- Isolated functionality verification
- Mock dependency testing

### Integration Tests
- API endpoint testing
- Database operation testing
- Service interaction testing

### Development Tools
- Database utilities
- Configuration helpers
- Migration scripts

## 🔧 Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Required for AI functionality tests
- `DATABASE_URL`: Database connection for testing
- `LOG_LEVEL`: Test logging verbosity

### Test Database
- Uses separate test database when possible
- Cleans up test data after execution
- Maintains production data integrity

## 📊 Test Results

### Success Indicators
- ✅ All tests pass
- ✅ No critical errors
- ✅ Performance within acceptable limits

### Common Issues
- Missing API keys
- Database connection failures
- Network connectivity problems

## 🤝 Contributing

### Adding New Tests
1. Follow existing test patterns
2. Include comprehensive error handling
3. Add clear documentation
4. Update this README

### Test Standards
- Clear test names and descriptions
- Proper setup and teardown
- Meaningful assertions
- Comprehensive coverage

---

**Note**: These are development and testing utilities. For production deployment, use the main platform files.
