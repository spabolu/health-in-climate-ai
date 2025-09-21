# HeatGuard Test Suite

Comprehensive test suite for the HeatGuard Predictive Safety System, ensuring production-grade quality and reliability for heat exposure prediction and worker safety monitoring.

## 🎯 Test Coverage Goals

- **>90% code coverage** across all modules
- **<200ms response time** for single predictions
- **Complete API endpoint validation** for all 7 required endpoints
- **OSHA compliance verification** and audit trail testing
- **Security and authentication** comprehensive testing
- **ML model accuracy validation** with all 50 HRV features

## 📁 Test Structure

```
backend/tests/
├── __init__.py                  # Test package initialization
├── conftest.py                  # Pytest configuration and global fixtures
├── pytest.ini                  # Pytest configuration file
├── run_tests.py                 # Comprehensive test runner
├── README.md                    # This documentation
├──
├── # Core Test Files
├── test_api_endpoints.py        # API endpoint functionality tests
├── test_heat_predictor.py       # ML model validation tests
├── test_auth.py                 # Authentication and security tests
├── test_performance.py          # Performance and load tests
├── test_integration.py          # End-to-end integration tests
├── test_compliance.py           # OSHA compliance and regulatory tests
├── test_services.py             # Service layer business logic tests
├── test_utils.py                # Utility functions and validation tests
├──
└── fixtures/                    # Test data and mocks
    ├── __init__.py
    ├── sample_data.py           # Sample test data with all 50 features
    └── mock_responses.py        # Mock API responses and test data
```

## 🚀 Quick Start

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Optional: For parallel execution
pip install pytest-xdist

# Optional: For performance testing
pip install psutil
```

### Running Tests

```bash
# Run all tests with coverage
python tests/run_tests.py

# Run specific test categories
python tests/run_tests.py --unit           # Unit tests only
python tests/run_tests.py --integration    # Integration tests only
python tests/run_tests.py --performance    # Performance tests only
python tests/run_tests.py --security       # Security tests only
python tests/run_tests.py --compliance     # OSHA compliance tests only

# Run tests in parallel (faster execution)
python tests/run_tests.py --parallel

# Run fast tests only (skip slow tests)
python tests/run_tests.py --fast

# Run specific test file
python tests/run_tests.py --file test_api_endpoints.py

# Check test requirements
python tests/run_tests.py --check

# List available test categories
python tests/run_tests.py --list
```

### Alternative Direct Pytest Commands

```bash
# Basic test execution
pytest

# With coverage reporting
pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific markers
pytest -m unit                    # Unit tests
pytest -m integration             # Integration tests
pytest -m performance             # Performance tests
pytest -m "not slow"              # Exclude slow tests

# Verbose output with detailed timing
pytest -v --durations=10

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

## 📊 Test Categories

### Unit Tests (`pytest -m unit`)
- Individual component testing
- ML model validation (HeatExposurePredictor)
- Utility function verification
- Data validation logic
- Configuration validation

### Integration Tests (`pytest -m integration`)
- Complete prediction pipeline testing
- Service integration verification
- Database and external service integration
- Error handling across service boundaries
- Full workflow simulation

### Performance Tests (`pytest -m performance`)
- Single prediction <200ms requirement
- Batch processing efficiency
- Concurrent request handling
- Memory usage optimization
- Load testing and scalability

### Security Tests (`pytest -m security`)
- API key authentication validation
- Rate limiting functionality
- Input sanitization and XSS protection
- SQL injection protection
- Security headers verification

### Compliance Tests (`pytest -m compliance`)
- OSHA compliance logging
- Regulatory requirement validation
- Audit trail integrity
- Incident reporting functionality
- Documentation generation

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)

The test suite is configured with:
- **90% minimum coverage** requirement
- **30-second timeout** for individual tests
- **Comprehensive markers** for test categorization
- **HTML and XML coverage reports**
- **Performance profiling** with duration reporting

### Environment Variables

```bash
export ENVIRONMENT=testing
export HEATGUARD_LOG_LEVEL=DEBUG
export HEATGUARD_TESTING=true
```

## 📋 API Endpoint Test Coverage

### Required Endpoints (All Tested)

1. **POST /api/v1/predict** - Single worker prediction
   - ✅ Success scenarios with all 50 features
   - ✅ Validation error handling
   - ✅ Authentication requirements
   - ✅ Performance <200ms validation

2. **POST /api/v1/predict_batch** - Batch worker predictions
   - ✅ Batch processing up to 1000 workers
   - ✅ Parallel processing validation
   - ✅ Partial failure handling
   - ✅ Batch statistics generation

3. **GET /api/v1/generate_random** - Random test data generation
   - ✅ Configurable sample counts
   - ✅ Risk distribution parameters
   - ✅ Reproducible seed-based generation

4. **GET /api/v1/generate_ramp_up** - Escalating risk scenarios
   - ✅ Progressive heat exposure simulation
   - ✅ Realistic physiological responses
   - ✅ Time-based progression validation

5. **GET /api/v1/generate_ramp_down** - De-escalating risk scenarios
   - ✅ Recovery pattern simulation
   - ✅ Cooling-down protocol testing

6. **GET /api/v1/health** - System health monitoring
   - ✅ Comprehensive health status
   - ✅ Service dependency checking
   - ✅ Performance metrics validation

7. **Additional Endpoints**
   - ✅ Async batch processing endpoints
   - ✅ Job status and results endpoints
   - ✅ System information endpoints

## 🧪 Test Data Features

### All 50 Required Features Tested

#### Demographics (2 features)
- `Age` - Worker age validation (18-65 years)
- `Gender` - Gender classification (0=Female, 1=Male)

#### Environmental (2 features)
- `Temperature` - Environmental temperature in Celsius
- `Humidity` - Relative humidity percentage (0-100)

#### HRV Features (46 features)
Complete heart rate variability metrics including:
- Time domain: `hrv_mean_nni`, `hrv_median_nni`, `hrv_rmssd`, `hrv_sdnn`, etc.
- Frequency domain: `hrv_lf`, `hrv_hf`, `hrv_lf_hf_ratio`, `hrv_total_power`, etc.
- Geometric measures: `hrv_triangular_index`, `hrv_tinn`, etc.
- Non-linear measures: `hrv_alpha1`, `hrv_alpha2`, etc.

### Test Scenarios

- **Safe Conditions** - Low risk baseline scenarios
- **High Risk Scenarios** - Dangerous heat exposure conditions
- **Edge Cases** - Boundary value testing
- **Invalid Data** - Malformed input validation
- **Missing Features** - Robustness with incomplete data
- **Realistic Workforce** - Diverse demographic profiles

## 🏥 OSHA Compliance Testing

### Compliance Features Tested

- **Automatic Logging** - All predictions logged for audit
- **Risk Assessment** - OSHA standard adherence validation
- **Work/Rest Cycles** - Recommendation compliance
- **Temperature Monitoring** - Threshold compliance
- **Incident Reporting** - Emergency response workflows
- **Documentation Generation** - Regulatory report creation
- **Audit Trail Integrity** - Tamper-evident logging

### Regulatory Standards Validated

- Heat index calculations per NOAA standards
- Work/rest ratios based on environmental conditions
- Hydration requirements for different risk levels
- Personal protective equipment recommendations
- Medical monitoring requirements

## ⚡ Performance Requirements

### Response Time Requirements

- **Single Predictions**: <200ms (strictly enforced)
- **Batch Processing**: Efficient throughput scaling
- **Health Checks**: <50ms for system status
- **Data Generation**: <100ms for test data

### Load Testing Scenarios

- Concurrent single predictions (10-50 simultaneous)
- Large batch processing (100-1000 workers)
- Mixed endpoint usage patterns
- Peak load handling and graceful degradation

## 🔒 Security Test Coverage

### Authentication Testing

- Valid API key authentication
- Invalid/expired key rejection
- Rate limiting per API key
- Permission-based access control
- Security header validation

### Input Security

- SQL injection protection
- Cross-site scripting (XSS) prevention
- Input sanitization validation
- Request size limiting
- Malformed JSON handling

## 📈 Coverage Reports

### Generating Coverage Reports

```bash
# HTML coverage report (recommended)
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Terminal coverage report
pytest --cov=app --cov-report=term-missing

# XML coverage report (for CI/CD)
pytest --cov=app --cov-report=xml
```

### Coverage Targets by Module

- **API Endpoints**: >95% coverage
- **ML Model**: >90% coverage
- **Authentication**: >95% coverage
- **Utilities**: >85% coverage
- **Services**: >90% coverage

## 🔄 Continuous Integration

### CI/CD Integration

```yaml
# Example GitHub Actions workflow
name: HeatGuard Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run test suite
      run: python tests/run_tests.py --report
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
-   repo: local
    hooks:
    -   id: tests
        name: run-tests
        entry: python tests/run_tests.py --fast
        language: system
        pass_filenames: false
```

## 🐛 Debugging Tests

### Common Issues and Solutions

1. **Model Loading Errors**
   ```bash
   # Ensure model files exist
   ls -la thermal_comfort_model/

   # Check model directory permissions
   chmod -R 755 thermal_comfort_model/
   ```

2. **Redis Connection Issues**
   ```bash
   # Start Redis server
   redis-server

   # Or disable Redis for testing
   export HEATGUARD_REDIS_URL=""
   ```

3. **Permission Errors**
   ```bash
   # Fix log file permissions
   chmod 644 logs/*.log
   ```

### Verbose Test Output

```bash
# Maximum verbosity
pytest -vvv --tb=long --show-capture=all

# Show print statements
pytest -s

# Drop into debugger on failures
pytest --pdb
```

## 📝 Writing New Tests

### Test File Template

```python
import pytest
from unittest.mock import Mock, patch

class TestNewFeature:
    """Test new feature functionality."""

    @pytest.fixture
    def sample_data(self):
        """Create sample test data."""
        return {"key": "value"}

    def test_feature_success(self, sample_data):
        """Test successful feature operation."""
        # Arrange
        expected_result = "success"

        # Act
        result = new_feature(sample_data)

        # Assert
        assert result == expected_result

    def test_feature_failure(self, sample_data):
        """Test feature error handling."""
        with pytest.raises(ValueError):
            new_feature(invalid_data)
```

### Best Practices

1. **Descriptive Test Names** - Clear indication of what's being tested
2. **Arrange-Act-Assert** - Structured test organization
3. **Mock External Dependencies** - Isolated unit testing
4. **Comprehensive Coverage** - Both success and failure cases
5. **Performance Considerations** - Include timing assertions where relevant
6. **Documentation** - Clear docstrings for test purposes

## 🎯 Test Metrics and Goals

### Quality Gates

| Metric | Target | Current Status |
|--------|---------|----------------|
| Code Coverage | >90% | 🎯 Target |
| API Response Time | <200ms | 🎯 Target |
| Test Success Rate | >99% | 🎯 Target |
| Security Tests | 100% Pass | 🎯 Target |
| OSHA Compliance | 100% Pass | 🎯 Target |

### Success Criteria

- ✅ All API endpoints tested with >95% coverage
- ✅ ML model validation with all 50 features
- ✅ Performance requirements met (<200ms)
- ✅ Security vulnerabilities addressed
- ✅ OSHA compliance verified
- ✅ Integration workflows validated
- ✅ Error handling comprehensive

## 🤝 Contributing

### Adding New Tests

1. **Create test file** following naming convention `test_*.py`
2. **Add appropriate markers** (`@pytest.mark.unit`, etc.)
3. **Include in test categories** as needed
4. **Update documentation** for new test coverage
5. **Verify coverage targets** are met

### Test Review Checklist

- [ ] Tests cover both success and failure scenarios
- [ ] Performance requirements validated where applicable
- [ ] Security implications considered
- [ ] OSHA compliance impact assessed
- [ ] Integration touchpoints verified
- [ ] Documentation updated

---

## 📞 Support

For questions about the test suite:

1. **Review test documentation** and inline comments
2. **Check existing issues** in the repository
3. **Run test diagnostics**: `python tests/run_tests.py --check`
4. **Contact the development team** for specific questions

**Remember**: This test suite ensures the safety and reliability of a system that protects workers from heat-related illness. Comprehensive testing is not just good practice—it's a safety imperative.