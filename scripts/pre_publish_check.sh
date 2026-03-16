#!/usr/bin/env bash

# Pre-publish verification script for internal-admin
# Run this script before publishing to PyPI to ensure everything is ready

set -e  # Exit on any error

echo "🔍 Pre-publish Checklist for internal-admin"
echo "==========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# 1. Check if virtual environment is activated
echo "1. Checking virtual environment..."
if [[ -n "$VIRTUAL_ENV" ]]; then
    check_pass "Virtual environment is activated"
else
    check_warn "Virtual environment not activated (recommended)"
fi
echo ""

# 2. Check if required files exist
echo "2. Checking required files..."
for file in "README.md" "LICENSE" "pyproject.toml" "CHANGELOG.md" "MANIFEST.in"; do
    if [[ -f "$file" ]]; then
        check_pass "$file exists"
    else
        check_fail "$file is missing"
    fi
done
echo ""

# 3. Check Python version
echo "3. Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
REQUIRED_MAJOR=3
REQUIRED_MINOR=10

CURRENT_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
CURRENT_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [[ $CURRENT_MAJOR -ge $REQUIRED_MAJOR && $CURRENT_MINOR -ge $REQUIRED_MINOR ]]; then
    check_pass "Python version $PYTHON_VERSION (>= 3.10)"
else
    check_fail "Python version $PYTHON_VERSION (requires >= 3.10)"
fi
echo ""

# 4. Check if build tools are installed
echo "4. Checking build tools..."
if python -c "import build" 2>/dev/null; then
    check_pass "build package is installed"
else
    check_fail "build package not installed (run: pip install build)"
fi

if python -c "import twine" 2>/dev/null; then
    check_pass "twine package is installed"
else
    check_warn "twine package not installed (optional, run: pip install twine)"
fi
echo ""

# 5. Run linting checks
echo "5. Running linting checks..."
if command -v black &> /dev/null; then
    if black --check internal_admin tests &> /dev/null; then
        check_pass "black formatting check passed"
    else
        check_fail "black formatting check failed (run: black internal_admin tests)"
    fi
else
    check_warn "black not installed"
fi

if command -v isort &> /dev/null; then
    if isort --check-only internal_admin tests &> /dev/null; then
        check_pass "isort check passed"
    else
        check_fail "isort check failed (run: isort internal_admin tests)"
    fi
else
    check_warn "isort not installed"
fi

if command -v ruff &> /dev/null; then
    if ruff check internal_admin tests &> /dev/null; then
        check_pass "ruff check passed"
    else
        check_fail "ruff check failed (run: ruff check internal_admin tests)"
    fi
else
    check_warn "ruff not installed"
fi
echo ""

# 6. Run tests
echo "6. Running tests..."
if command -v pytest &> /dev/null; then
    if pytest tests/ -q &> /dev/null; then
        check_pass "All tests passed"
    else
        check_fail "Some tests failed (run: pytest tests/ -v)"
    fi
else
    check_warn "pytest not installed"
fi
echo ""

# 7. Check version consistency
echo "7. Checking version consistency..."
VERSION_TOML=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
VERSION_INIT=$(grep '^__version__ = ' internal_admin/__init__.py | cut -d'"' -f2)

if [[ "$VERSION_TOML" == "$VERSION_INIT" ]]; then
    check_pass "Version consistent: $VERSION_TOML"
else
    check_fail "Version mismatch: pyproject.toml ($VERSION_TOML) vs __init__.py ($VERSION_INIT)"
fi
echo ""

# 8. Build the package
echo "8. Building package..."
if python -m build &> /tmp/build.log; then
    check_pass "Package built successfully"
    
    # Check wheel contents
    if unzip -l dist/*.whl | grep -q "internal_admin/static"; then
        check_pass "Static files included in wheel"
    else
        check_fail "Static files missing from wheel"
    fi
    
    if unzip -l dist/*.whl | grep -q "internal_admin/templates"; then
        check_pass "Template files included in wheel"
    else
        check_fail "Template files missing from wheel"
    fi
else
    check_fail "Package build failed (check /tmp/build.log)"
fi
echo ""

# 9. Check package with twine
echo "9. Validating package with twine..."
if command -v twine &> /dev/null; then
    if twine check dist/* &> /dev/null; then
        check_pass "Package validation passed"
    else
        check_fail "Package validation failed"
    fi
else
    check_warn "twine not available, skipping validation"
fi
echo ""

# Summary
echo ""
echo "==========================================="
echo "Summary:"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}✓ Package is ready for publishing!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review PUBLISHING.md for publishing instructions"
    echo "  2. Commit changes using conventional commits"
    echo "  3. Push to main branch to trigger automatic release"
    echo "  OR"
    echo "  Manual publish: twine upload dist/*"
    exit 0
else
    echo -e "${RED}✗ Please fix the failed checks before publishing${NC}"
    exit 1
fi
